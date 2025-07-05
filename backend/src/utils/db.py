from typing import Any, Dict, List, Optional, TypeVar, Generic
from fastapi import HTTPException, status
from src.core.supabase_client import get_supabase_client, get_supabase_admin_client

T = TypeVar('T')

class Database:
    """
    Database utility class for Supabase operations.
    """
    
    @staticmethod
    def get_client(admin: bool = False):
        """
        Get the Supabase client.
        
        Args:
            admin: If True, returns the admin client with service role key.
        """
        if admin:
            return get_supabase_admin_client()
        return get_supabase_client()
    
    @staticmethod
    def _validate_response(response, method_name: str, strict: bool = True):
        """
        Validate that the response is not None and has the expected structure.
        
        Args:
            response: The response from Supabase
            method_name: Name of the calling method for error context
            strict: If True, raises exception on invalid response. If False, returns None.
            
        Returns:
            The response if valid, None if invalid and not strict
            
        Raises:
            HTTPException: If response is invalid and strict=True
        """
        if response is None:
            if strict:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database {method_name}: Received null response from database"
                )
            return None
        
        if not hasattr(response, 'data'):
            if strict:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database {method_name}: Response does not have 'data' attribute"
                )
            return None
        
        return response
    
    @staticmethod
    def select(table: str, columns: str = "*", filters: Optional[Dict[str, Any]] = None, 
               limit: Optional[int] = None, order_by: Optional[str] = None, strict: bool = True) -> List[Dict[str, Any]]:
        """
        Select data from a table.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dictionary of filters to apply
            limit: Maximum number of records to return
            order_by: Column to order by
            strict: If True, raises exception on invalid response. If False, returns empty list.
            
        Returns:
            List of records
        """
        try:
            client = Database.get_client()
            query = client.table(table).select(columns)
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Apply limit if provided
            if limit:
                query = query.limit(limit)
            
            # Apply order by if provided
            if order_by:
                # Parse the order_by string to handle direction properly
                if "." in order_by:
                    column, direction = order_by.split(".", 1)
                    if direction == "desc":
                        query = query.order(column, desc=True)
                    elif direction == "asc":
                        query = query.order(column, desc=False)
                    else:
                        # Default to ascending if direction is not recognized
                        query = query.order(column, desc=False)
                else:
                    # If no direction specified, default to ascending
                    query = query.order(order_by, desc=False)
            
            response = query.execute()
            validated_response = Database._validate_response(response, "select", strict)
            if validated_response is None:
                return []
            return validated_response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def select_tolerant(table: str, columns: str = "*", filters: Optional[Dict[str, Any]] = None, 
                       limit: Optional[int] = None, order_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Select data from a table with tolerant error handling.
        Returns empty list on any database errors.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dictionary of filters to apply
            limit: Maximum number of records to return
            order_by: Column to order by
            
        Returns:
            List of records or empty list on error
        """
        return Database.select(table, columns, filters, limit, order_by, strict=False)
    
    @staticmethod
    def select_paginated(table: str, page: int = 1, page_size: int = 10, 
                        columns: str = "*", filters: Optional[Dict[str, Any]] = None,
                        order_by: Optional[str] = None, count: bool = True, strict: bool = True) -> Dict[str, Any]:
        """
        Select data from a table with pagination.
        
        Args:
            table: Table name
            page: Page number (starts from 1)
            page_size: Number of items per page
            columns: Columns to select (default: "*")
            filters: Dictionary of filters to apply
            order_by: Column to order by
            count: Whether to include total count
            strict: If True, raises exception on invalid response. If False, returns empty data.
            
        Returns:
            Dictionary with data, total count, page, and page_size
        """
        try:
            client = Database.get_client()
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Build query
            query = client.table(table).select(columns)
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Get total count if requested
            total = 0
            if count:
                count_query = client.table(table).select("*", count="exact")
                if filters:
                    for key, value in filters.items():
                        count_query = count_query.eq(key, value)
                count_response = count_query.execute()
                validated_count_response = Database._validate_response(count_response, "select_paginated_count", strict)
                if validated_count_response is not None:
                    total = validated_count_response.count if validated_count_response.count is not None else 0
            
            # Apply ordering first, then pagination
            if order_by:
                # Parse the order_by string to handle direction properly
                if "." in order_by:
                    column, direction = order_by.split(".", 1)
                    if direction == "desc":
                        query = query.order(column, desc=True)
                    elif direction == "asc":
                        query = query.order(column, desc=False)
                    else:
                        # Default to ascending if direction is not recognized
                        query = query.order(column, desc=False)
                else:
                    # If no direction specified, default to ascending
                    query = query.order(order_by, desc=False)
            
            # Apply pagination
            query = query.range(offset, offset + page_size - 1)
            
            response = query.execute()
            validated_response = Database._validate_response(response, "select_paginated", strict)
            
            if validated_response is None:
                return {
                    "data": [],
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            
            return {
                "data": validated_response.data,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def select_paginated_tolerant(table: str, page: int = 1, page_size: int = 10, 
                                columns: str = "*", filters: Optional[Dict[str, Any]] = None,
                                order_by: Optional[str] = None, count: bool = True) -> Dict[str, Any]:
        """
        Select data from a table with pagination and tolerant error handling.
        Returns empty data on any database errors.
        
        Args:
            table: Table name
            page: Page number (starts from 1)
            page_size: Number of items per page
            columns: Columns to select (default: "*")
            filters: Dictionary of filters to apply
            order_by: Column to order by
            count: Whether to include total count
            
        Returns:
            Dictionary with data, total count, page, and page_size or empty data on error
        """
        return Database.select_paginated(table, page, page_size, columns, filters, order_by, count, strict=False)
    
    @staticmethod
    def insert(table: str, data: Dict[str, Any], strict: bool = True) -> Optional[Dict[str, Any]]:
        """
        Insert data into a table.
        
        Args:
            table: Table name
            data: Data to insert
            strict: If True, raises exception on invalid response. If False, returns None.
            
        Returns:
            Inserted record or None on error if not strict
        """
        try:
            client = Database.get_client()
            response = client.table(table).insert(data).execute()
            validated_response = Database._validate_response(response, "insert", strict)
            if validated_response is None:
                return None
            return validated_response.data[0] if validated_response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def insert_tolerant(table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert data into a table with tolerant error handling.
        Returns None on any database errors.
        
        Args:
            table: Table name
            data: Data to insert
            
        Returns:
            Inserted record or None on error
        """
        return Database.insert(table, data, strict=False)
    
    @staticmethod
    def update(table: str, data: Dict[str, Any], filters: Dict[str, Any], strict: bool = True) -> List[Dict[str, Any]]:
        """
        Update data in a table.
        
        Args:
            table: Table name
            data: Data to update
            filters: Dictionary of filters to apply
            strict: If True, raises exception on invalid response. If False, returns empty list.
            
        Returns:
            Updated records
        """
        try:
            client = Database.get_client()
            query = client.table(table).update(data)
            
            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            validated_response = Database._validate_response(response, "update", strict)
            if validated_response is None:
                return []
            return validated_response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def update_tolerant(table: str, data: Dict[str, Any], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Update data in a table with tolerant error handling.
        Returns empty list on any database errors.
        
        Args:
            table: Table name
            data: Data to update
            filters: Dictionary of filters to apply
            
        Returns:
            Updated records or empty list on error
        """
        return Database.update(table, data, filters, strict=False)
    
    @staticmethod
    def delete(table: str, filters: Dict[str, Any], strict: bool = True) -> List[Dict[str, Any]]:
        """
        Delete data from a table.
        
        Args:
            table: Table name
            filters: Dictionary of filters to apply
            strict: If True, raises exception on invalid response. If False, returns empty list.
            
        Returns:
            Deleted records
        """
        try:
            client = Database.get_client()
            query = client.table(table).delete()
            
            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            validated_response = Database._validate_response(response, "delete", strict)
            if validated_response is None:
                return []
            return validated_response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def delete_tolerant(table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Delete data from a table with tolerant error handling.
        Returns empty list on any database errors.
        
        Args:
            table: Table name
            filters: Dictionary of filters to apply
            
        Returns:
            Deleted records or empty list on error
        """
        return Database.delete(table, filters, strict=False)
    
    @staticmethod
    def select_single(table: str, columns: str = "*", filters: Optional[Dict[str, Any]] = None, strict: bool = True) -> Optional[Dict[str, Any]]:
        """
        Select a single record from a table.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dictionary of filters to apply
            strict: If True, raises exception on invalid response. If False, returns None.
            
        Returns:
            Single record or None if not found
        """
        try:
            client = Database.get_client()
            query = client.table(table).select(columns)
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.maybe_single().execute()
            validated_response = Database._validate_response(response, "select_single", strict)
            if validated_response is None:
                return None
            return validated_response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def select_single_tolerant(table: str, columns: str = "*", filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Select a single record from a table with tolerant error handling.
        Returns None on any database errors.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dictionary of filters to apply
            
        Returns:
            Single record or None if not found or on error
        """
        return Database.select_single(table, columns, filters, strict=False)
    
    @staticmethod
    def select_with_exclusions(table: str, columns: str = "*", 
                             filters: Optional[Dict[str, Any]] = None,
                             exclusions: Optional[Dict[str, Any]] = None, strict: bool = True) -> List[Dict[str, Any]]:
        """
        Select data from a table with exclusions (not equal conditions).
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dictionary of equality filters to apply
            exclusions: Dictionary of not-equal filters to apply
            strict: If True, raises exception on invalid response. If False, returns empty list.
            
        Returns:
            List of records
        """
        try:
            client = Database.get_client()
            query = client.table(table).select(columns)
            
            # Apply equality filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Apply exclusion filters if provided
            if exclusions:
                for key, value in exclusions.items():
                    query = query.neq(key, value)
            
            response = query.execute()
            validated_response = Database._validate_response(response, "select_with_exclusions", strict)
            if validated_response is None:
                return []
            return validated_response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def select_with_exclusions_tolerant(table: str, columns: str = "*", 
                                      filters: Optional[Dict[str, Any]] = None,
                                      exclusions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Select data from a table with exclusions and tolerant error handling.
        Returns empty list on any database errors.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dictionary of equality filters to apply
            exclusions: Dictionary of not-equal filters to apply
            
        Returns:
            List of records or empty list on error
        """
        return Database.select_with_exclusions(table, columns, filters, exclusions, strict=False)
    
    @staticmethod
    def insert_with_returning(table: str, data: Dict[str, Any], returning: str = "representation", strict: bool = True) -> Optional[Dict[str, Any]]:
        """
        Insert data into a table with returning clause.
        
        Args:
            table: Table name
            data: Data to insert
            returning: What to return (default: "representation")
            strict: If True, raises exception on invalid response. If False, returns None.
            
        Returns:
            Inserted record or None on error if not strict
        """
        try:
            client = Database.get_client()
            response = client.table(table).insert(data, returning=returning).execute()
            validated_response = Database._validate_response(response, "insert_with_returning", strict)
            if validated_response is None:
                return None
            return validated_response.data[0] if validated_response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def insert_with_returning_tolerant(table: str, data: Dict[str, Any], returning: str = "representation") -> Optional[Dict[str, Any]]:
        """
        Insert data into a table with returning clause and tolerant error handling.
        Returns None on any database errors.
        
        Args:
            table: Table name
            data: Data to insert
            returning: What to return (default: "representation")
            
        Returns:
            Inserted record or None on error
        """
        return Database.insert_with_returning(table, data, returning, strict=False)
    
    @staticmethod
    def select_with_ilike(table: str, columns: str = "*", 
                         ilike_filters: Optional[Dict[str, str]] = None,
                         filters: Optional[Dict[str, Any]] = None,
                         exclusions: Optional[Dict[str, Any]] = None,
                         page: int = 1, page_size: int = 10,
                         order_by: Optional[str] = None, count: bool = True, strict: bool = True) -> Dict[str, Any]:
        """
        Select data from a table with ILIKE (case-insensitive partial matching) support.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            ilike_filters: Dictionary of ILIKE filters for partial matching
            filters: Dictionary of equality filters to apply
            exclusions: Dictionary of not-equal filters to apply
            page: Page number (starts from 1)
            page_size: Number of items per page
            order_by: Column to order by
            count: Whether to include total count
            strict: If True, raises exception on invalid response. If False, returns empty data.
            
        Returns:
            Dictionary with data, total count, page, and page_size
        """
        try:
            client = Database.get_client()
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Build query
            query = client.table(table).select(columns)
            
            # Apply equality filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Apply exclusion filters if provided
            if exclusions:
                for key, value in exclusions.items():
                    query = query.neq(key, value)
            
            # Apply ILIKE filters if provided
            if ilike_filters:
                for key, value in ilike_filters.items():
                    query = query.ilike(key, f'%{value}%')
            
            # Get total count if requested
            total = 0
            if count:
                count_query = client.table(table).select("*", count="exact")
                if filters:
                    for key, value in filters.items():
                        count_query = count_query.eq(key, value)
                if exclusions:
                    for key, value in exclusions.items():
                        count_query = count_query.neq(key, value)
                if ilike_filters:
                    for key, value in ilike_filters.items():
                        count_query = count_query.ilike(key, f'%{value}%')
                count_response = count_query.execute()
                validated_count_response = Database._validate_response(count_response, "select_with_ilike_count", strict)
                if validated_count_response is not None:
                    total = validated_count_response.count if validated_count_response.count is not None else 0
            
            # Apply pagination and ordering
            query = query.range(offset, offset + page_size - 1)
            if order_by:
                query = query.order(order_by)
            
            response = query.execute()
            validated_response = Database._validate_response(response, "select_with_ilike", strict)
            
            if validated_response is None:
                return {
                    "data": [],
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            
            return {
                "data": validated_response.data,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def select_with_ilike_tolerant(table: str, columns: str = "*", 
                                 ilike_filters: Optional[Dict[str, str]] = None,
                                 filters: Optional[Dict[str, Any]] = None,
                                 exclusions: Optional[Dict[str, Any]] = None,
                                 page: int = 1, page_size: int = 10,
                                 order_by: Optional[str] = None, count: bool = True) -> Dict[str, Any]:
        """
        Select data from a table with ILIKE and tolerant error handling.
        Returns empty data on any database errors.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            ilike_filters: Dictionary of ILIKE filters for partial matching
            filters: Dictionary of equality filters to apply
            exclusions: Dictionary of not-equal filters to apply
            page: Page number (starts from 1)
            page_size: Number of items per page
            order_by: Column to order by
            count: Whether to include total count
            
        Returns:
            Dictionary with data, total count, page, and page_size or empty data on error
        """
        return Database.select_with_ilike(table, columns, ilike_filters, filters, exclusions, page, page_size, order_by, count, strict=False) 