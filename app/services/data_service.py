"""
DataService - Python's equivalent of Axios for database operations
Reusable database service layer para sa lahat ng database operations
Now with pagination support!
"""

import mysql.connector
from typing import List, Dict, Any, Optional, Tuple
from app.utils.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from app.services.pagination import PaginationParams, PaginationResult, PaginationService
import logging

class DataService:
    """
    Reusable database service - parang axios pero for database
    Provides common CRUD operations na pwedeng gamitin anywhere
    """
    
    @staticmethod
    def get_connection():
        """Get database connection"""
        try:
            return mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True
            )
        except mysql.connector.Error as e:
            print(f"❌ Database connection error: {e}")
            return None
    
    @staticmethod
    def execute_query(query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """
        Execute SQL query and return results
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            fetch: Whether to fetch results (default True)
            
        Returns:
            List of dictionaries for SELECT queries, None for INSERT/UPDATE/DELETE
        """
        conn = DataService.get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                results = cursor.fetchall()
                cursor.close()
                conn.close()
                return results
            else:
                affected_rows = cursor.rowcount
                cursor.close()
                conn.close()
                return affected_rows
                
        except mysql.connector.Error as e:
            print(f"❌ Query execution error: {e}")
            if conn:
                conn.close()
            return None
    
    # CRUD Operations - Generic methods
    
    @staticmethod
    def get_all(table: str, order_by: str = None) -> List[Dict]:
        """SELECT * FROM table"""
        query = f"SELECT * FROM {table}"
        if order_by:
            query += f" ORDER BY {order_by}"
        
        results = DataService.execute_query(query)
        return results or []
    
    @staticmethod
    def get_by_id(table: str, id_value: Any, id_column: str = "id") -> Optional[Dict]:
        """SELECT * FROM table WHERE id = ?"""
        query = f"SELECT * FROM {table} WHERE {id_column} = %s"
        results = DataService.execute_query(query, (id_value,))
        return results[0] if results else None
    
    @staticmethod
    def create(table: str, data: Dict) -> bool:
        """INSERT INTO table"""
        if not data:
            return False
            
        columns = list(data.keys())
        placeholders = ', '.join(['%s'] * len(columns))
        values = list(data.values())
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        result = DataService.execute_query(query, tuple(values), fetch=False)
        return result is not None and result > 0
    
    @staticmethod
    def update(table: str, id_value: Any, data: Dict, id_column: str = "id") -> bool:
        """UPDATE table SET ... WHERE id = ?"""
        if not data:
            return False
            
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        values = list(data.values()) + [id_value]
        
        query = f"UPDATE {table} SET {set_clause} WHERE {id_column} = %s"
        result = DataService.execute_query(query, tuple(values), fetch=False)
        return result is not None and result > 0
    
    @staticmethod
    def delete(table: str, id_value: Any, id_column: str = "id") -> bool:
        """DELETE FROM table WHERE id = ?"""
        query = f"DELETE FROM {table} WHERE {id_column} = %s"
        result = DataService.execute_query(query, (id_value,), fetch=False)
        return result is not None and result > 0
    
    # Advanced query methods
    
    @staticmethod
    def search(table: str, search_term: str, columns: List[str]) -> List[Dict]:
        """Search in multiple columns"""
        if not search_term or not columns:
            return DataService.get_all(table)
            
        where_clause = ' OR '.join([f"{col} LIKE %s" for col in columns])
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        params = tuple([f"%{search_term}%"] * len(columns))
        
        results = DataService.execute_query(query, params)
        return results or []
    
    @staticmethod
    def count(table: str, where_clause: str = None, params: tuple = None) -> int:
        """COUNT rows in table"""
        query = f"SELECT COUNT(*) as count FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
            
        result = DataService.execute_query(query, params)
        return result[0]['count'] if result else 0
    
    @staticmethod
    def get_with_join(query: str, params: tuple = None) -> List[Dict]:
        """Execute custom JOIN queries"""
        results = DataService.execute_query(query, params)
        return results or []
    
    # ========== PAGINATION METHODS ==========
    
    @staticmethod
    def get_paginated(
        table_name: str,
        pagination_params: PaginationParams,
        columns: List[str] = None,
        search_columns: List[str] = None,
        allowed_sort_columns: List[str] = None
    ) -> PaginationResult:
        """
        Get paginated data from a table - like axios with pagination
        
        Args:
            table_name: Name of the table
            pagination_params: Pagination parameters
            columns: Columns to select (default: *)
            search_columns: Columns to search in
            allowed_sort_columns: Allowed columns for sorting
        
        Returns:
            PaginationResult with data and metadata
        """
        try:
            # Build column list
            column_list = ", ".join(columns) if columns else "*"
            
            # Build WHERE clause
            where_clause, where_params = PaginationService.build_where_clause(
                pagination_params, search_columns
            )
            
            # Build ORDER BY clause
            order_clause = PaginationService.build_order_clause(
                pagination_params, allowed_sort_columns
            )
            
            # Build LIMIT clause
            limit_clause = PaginationService.build_limit_clause(pagination_params)
            
            # Build data query
            data_query = f"""
                SELECT {column_list}
                FROM {table_name}
                {where_clause}
                {order_clause}
                {limit_clause}
            """
            
            # Build count query
            count_query = f"""
                SELECT COUNT(*)
                FROM {table_name}
                {where_clause}
            """
            
            # Execute queries
            data_results = DataService.execute_query(data_query, tuple(where_params))
            count_result = DataService.execute_query(count_query, tuple(where_params))
            
            # Extract total count
            total_count = count_result[0].get('COUNT(*)', 0) if count_result else 0
            
            # Create pagination result
            return PaginationResult.from_params(
                data=data_results or [],
                total_count=total_count,
                params=pagination_params
            )
            
        except Exception as e:
            print(f"❌ Pagination error: {e}")
            return PaginationResult.from_params([], 0, pagination_params)
    
    @staticmethod
    def get_paginated_with_query(
        base_query: str,
        pagination_params: PaginationParams,
        query_params: tuple = None,
        allowed_sort_columns: List[str] = None
    ) -> PaginationResult:
        """
        Get paginated data with custom query - for complex JOINs
        
        Args:
            base_query: Base SELECT query (without ORDER BY, LIMIT)
            pagination_params: Pagination parameters
            query_params: Parameters for the base query
            allowed_sort_columns: Allowed columns for sorting
        
        Returns:
            PaginationResult with data and metadata
        """
        try:
            # Build ORDER BY clause
            order_clause = PaginationService.build_order_clause(
                pagination_params, allowed_sort_columns
            )
            
            # Build LIMIT clause
            limit_clause = PaginationService.build_limit_clause(pagination_params)
            
            # Build full query
            data_query = f"{base_query} {order_clause} {limit_clause}"
            
            # Build count query
            count_query = PaginationService.build_count_query(base_query)
            
            # Execute queries
            data_results = DataService.execute_query(data_query, query_params)
            count_result = DataService.execute_query(count_query, query_params)
            
            # Extract total count
            total_count = count_result[0].get('COUNT(*)', 0) if count_result else 0
            
            # Create pagination result
            return PaginationResult.from_params(
                data=data_results or [],
                total_count=total_count,
                params=pagination_params
            )
            
        except Exception as e:
            print(f"❌ Custom pagination error: {e}")
            return PaginationResult.from_params([], 0, pagination_params)

# Test connection function
def test_connection():
    """Test database connection"""
    conn = DataService.get_connection()
    if conn:
        print("✅ Database connection successful!")
        conn.close()
        return True
    else:
        print("❌ Database connection failed!")
        return False

if __name__ == "__main__":
    # Test the connection
    test_connection()
