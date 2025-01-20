import json
import boto3
import cfnresponse
import logging
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cloudwatch = boto3.client('cloudwatch')

def sort_widgets_by_type(widgets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sorts widgets by type, with timeseries first, then tables"""
    timeseries_widgets = []
    table_widgets = []
    other_widgets = []
    
    for widget in widgets:
        # Get the properties dictionary that contains the view type
        properties = widget.get('properties', {})
        view = properties.get('view', '')
        
        if view == 'timeseries':
            timeseries_widgets.append(widget)
        elif view == 'table':
            table_widgets.append(widget)
        else:
            other_widgets.append(widget)
    
    return timeseries_widgets + table_widgets + other_widgets

def adjust_widget_positions(widgets: List[Dict[str, Any]], start_y: int = 0) -> List[Dict[str, Any]]:
    """Adjusts widget positions to be vertically stacked from a starting y-position"""
    current_y = start_y
    adjusted_widgets = []
    
    for widget in widgets:
        widget_copy = widget.copy()
        widget_copy['y'] = current_y
        adjusted_widgets.append(widget_copy)
        current_y += widget_copy.get('height', 0)
    
    return adjusted_widgets

def merge_dashboard_bodies(dashboard_1_body: str, dashboard_2_body: str) -> Dict[str, Any]:
    """Merges two dashboard JSON bodies by combining their widgets, grouped by type"""
    try:
        dashboard_1 = json.loads(dashboard_1_body)
        dashboard_2 = json.loads(dashboard_2_body)
            
        # Initialize widgets lists if not present
        dashboard_1.setdefault('widgets', [])
        dashboard_2.setdefault('widgets', [])
        
        # Combine all widgets from both dashboards
        all_widgets = dashboard_1['widgets'] + dashboard_2['widgets']
        
        # Sort widgets by type
        sorted_widgets = sort_widgets_by_type(all_widgets)
        
        # Adjust positions to stack them vertically
        positioned_widgets = adjust_widget_positions(sorted_widgets)
        
        # Create merged dashboard
        merged_dashboard = dashboard_1.copy()
        merged_dashboard['widgets'] = positioned_widgets
            
        return merged_dashboard
        
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding dashboard JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Error merging dashboards: {e}")
        raise

def get_dashboard_body(dashboard_name: str) -> Optional[str]:
    """Gets the dashboard body from CloudWatch"""
    try:
        response = cloudwatch.get_dashboard(DashboardName=dashboard_name)
        return response['DashboardBody']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFound':
            logger.warning(f"Dashboard {dashboard_name} not found")
            return None
        logger.error(f"Error getting dashboard {dashboard_name}: {e}")
        raise

def create_or_update_dashboard(dashboard_name: str, dashboard_body: Dict[str, Any]) -> None:
    """Creates or updates a CloudWatch dashboard"""
    try:
        cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
    except Exception as e:
        logger.error(f"Error creating/updating dashboard: {e}")
        raise

def delete_dashboard(dashboard_name: str) -> None:
    """Deletes a CloudWatch dashboard"""
    try:
        cloudwatch.delete_dashboards(DashboardNames=[dashboard_name])
    except Exception as e:
        logger.error(f"Error deleting dashboard: {e}")
        # Don't raise - best effort deletion

def handler(event: Dict[str, Any], context: Any) -> None:
    """Custom resource handler that merges and creates/updates dashboard"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        request_type = event['RequestType']
        props = event.get('ResourceProperties', {})
            
        merged_dashboard_name = props.get('MergedDashboardName')
        if not merged_dashboard_name:
            raise ValueError("MergedDashboardName is required")
        
        # On delete, clean up the dashboard
        if request_type == 'Delete':
            delete_dashboard(merged_dashboard_name)
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, physicalResourceId=merged_dashboard_name)
            return
            
        dashboard_1_name = props.get('Dashboard1Name')
        dashboard_2_name = props.get('Dashboard2Name')
        
        if not dashboard_1_name or not dashboard_2_name:
            raise ValueError("Dashboard1Name and Dashboard2Name are required")
            
        # Get dashboard bodies
        dashboard_1_body = get_dashboard_body(dashboard_1_name)
        if not dashboard_1_body:
            raise ValueError(f"Dashboard 1 {dashboard_1_name} not found")
            
        dashboard_2_body = get_dashboard_body(dashboard_2_name)
        if not dashboard_2_body:
            raise ValueError(f"Dashboard 2 {dashboard_2_name} not found")
        
        # Merge dashboards
        merged_dash = merge_dashboard_bodies(dashboard_1_body, dashboard_2_body)
        
        # Log the merged dashboard JSON
        logger.info(f"Merged dashboard JSON: {json.dumps(merged_dash, indent=2)}")
        
        # Create or update the merged dashboard
        create_or_update_dashboard(merged_dashboard_name, merged_dash)
        
        # Return success with the dashboard name and set the physical resource ID
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {
            'DashboardName': merged_dashboard_name
        }, physicalResourceId=merged_dashboard_name)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        # Pass the physical resource ID even in case of failure
        cfnresponse.send(event, context, cfnresponse.FAILED, {
            'Error': str(e)
        }, physicalResourceId=props.get('MergedDashboardName', 'INVALID'))