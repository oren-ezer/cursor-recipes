from typing import Any, Dict, List, Optional, TypeVar, Generic
from fastapi import HTTPException, status
from app.core.supabase_client import get_supabase_client, get_supabase_admin_client

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
    def select(table: str, columns: str = "*", filters: Optional[Dict[str, Any]] = None, 
               limit: Optional[int] = None, order_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Select data from a table.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dictionary of filters to apply
            limit: Maximum number of records to return
            order_by: Column to order by
            
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
                query = query.order(order_by)
            
            response = query.execute()
            return response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def insert(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert data into a table.
        
        Args:
            table: Table name
            data: Data to insert
            
        Returns:
            Inserted record
        """
        try:
            client = Database.get_client()
            response = client.table(table).insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def update(table: str, data: Dict[str, Any], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Update data in a table.
        
        Args:
            table: Table name
            data: Data to update
            filters: Dictionary of filters to apply
            
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
            return response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def delete(table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Delete data from a table.
        
        Args:
            table: Table name
            filters: Dictionary of filters to apply
            
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
            return response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            ) 