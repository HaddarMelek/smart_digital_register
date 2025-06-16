"""
Standardized API Response Utilities
Ensures all APIs return consistent response formats
"""

from flask import jsonify
from typing import Any, Dict, Optional, List


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    meta: Optional[Dict] = None
) -> tuple:
    """
    Create a standardized success response
    
    Args:
        data: The response data (can be dict, list, etc.)
        message: Success message
        status_code: HTTP status code
        meta: Additional metadata (pagination, counts, etc.)
    
    Returns:
        tuple: (response, status_code)
    """
    response = {
        "success": True,
        "message": message,
        "data": data
    }
    
    if meta:
        response["meta"] = meta
    
    return jsonify(response), status_code


def error_response(
    message: str = "An error occurred",
    status_code: int = 400,
    errors: Optional[List[str]] = None,
    error_code: Optional[str] = None
) -> tuple:
    """
    Create a standardized error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        errors: List of detailed errors
        error_code: Specific error code for frontend handling
    
    Returns:
        tuple: (response, status_code)
    """
    response = {
        "success": False,
        "message": message,
        "data": None
    }
    
    if errors:
        response["errors"] = errors
    
    if error_code:
        response["error_code"] = error_code
    
    return jsonify(response), status_code


def paginated_response(
    data: List,
    page: int,
    per_page: int,
    total: int,
    message: str = "Data retrieved successfully"
) -> tuple:
    """
    Create a paginated response
    
    Args:
        data: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        message: Success message
    
    Returns:
        tuple: (response, status_code)
    """
    total_pages = (total + per_page - 1) // per_page
    
    meta = {
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
    
    return success_response(
        data=data,
        message=message,
        meta=meta
    )


def validation_error_response(errors: List[str]) -> tuple:
    """
    Create a validation error response
    
    Args:
        errors: List of validation errors
    
    Returns:
        tuple: (response, status_code)
    """
    return error_response(
        message="Validation failed",
        status_code=400,
        errors=errors,
        error_code="VALIDATION_ERROR"
    )


def not_found_response(resource: str = "Resource") -> tuple:
    """
    Create a not found error response
    
    Args:
        resource: Name of the resource that wasn't found
    
    Returns:
        tuple: (response, status_code)
    """
    return error_response(
        message=f"{resource} not found",
        status_code=404,
        error_code="NOT_FOUND"
    )


def unauthorized_response(message: str = "Unauthorized access") -> tuple:
    """
    Create an unauthorized error response
    
    Args:
        message: Unauthorized message
    
    Returns:
        tuple: (response, status_code)
    """
    return error_response(
        message=message,
        status_code=401,
        error_code="UNAUTHORIZED"
    )


def forbidden_response(message: str = "Access forbidden") -> tuple:
    """
    Create a forbidden error response
    
    Args:
        message: Forbidden message
    
    Returns:
        tuple: (response, status_code)
    """
    return error_response(
        message=message,
        status_code=403,
        error_code="FORBIDDEN"
    )


def server_error_response(message: str = "Internal server error") -> tuple:
    """
    Create a server error response
    
    Args:
        message: Error message
    
    Returns:
        tuple: (response, status_code)
    """
    return error_response(
        message=message,
        status_code=500,
        error_code="INTERNAL_ERROR"
    )