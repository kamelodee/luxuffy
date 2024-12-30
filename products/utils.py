from rest_framework.response import Response
from rest_framework import status

def create_response(data=None, message=None, status_code=status.HTTP_200_OK):
    """
    Create a standardized API response.
    
    Args:
        data: Response data (optional)
        message: Response message (optional)
        status_code: HTTP status code (default: 200)
    
    Returns:
        Response object with standardized format
    """
    response_data = {
        'status_code': status_code,
        'message': message,
        'data': data
    }
    return Response(response_data, status=status_code)
