"""
Pagination Service - Reusable pagination for database queries
Like axios with pagination parameters in web development
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class PaginationParams:
    """Pagination parameters"""
    page: int = 1
    limit: int = 25
    sort_by: str = "id"
    sort_order: str = "ASC"  # ASC or DESC
    search_term: str = ""
    filters: Dict[str, Any] = None
    
    def __post_init__(self):
        # Ensure page is at least 1
        if self.page < 1:
            self.page = 1
        
        # Ensure limit is reasonable (between 5 and 100)
        if self.limit < 5:
            self.limit = 5
        elif self.limit > 100:
            self.limit = 100
        
        # Validate sort order
        if self.sort_order.upper() not in ["ASC", "DESC"]:
            self.sort_order = "ASC"
        
        # Initialize filters if None
        if self.filters is None:
            self.filters = {}
    
    @property
    def offset(self) -> int:
        """Calculate OFFSET for SQL queries"""
        return (self.page - 1) * self.limit
    
    def to_sql_params(self) -> Dict[str, Any]:
        """Convert to SQL parameters"""
        return {
            "limit": self.limit,
            "offset": self.offset,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order.upper()
        }

@dataclass
class PaginationResult:
    """Pagination result with data and metadata"""
    data: List[Any]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def from_params(cls, data: List[Any], total_count: int, params: PaginationParams):
        """Create PaginationResult from data and params"""
        total_pages = (total_count + params.limit - 1) // params.limit  # Ceiling division
        
        return cls(
            data=data,
            total_count=total_count,
            page=params.page,
            limit=params.limit,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_prev=params.page > 1
        )
    
    def get_page_info(self) -> str:
        """Get human-readable page info"""
        start = (self.page - 1) * self.limit + 1
        end = min(start + self.limit - 1, self.total_count)
        
        if self.total_count == 0:
            return "No records found"
        
        return f"Showing {start}-{end} of {self.total_count:,} records"
    
    def get_page_numbers(self, window: int = 5) -> List[int]:
        """Get page numbers for pagination controls"""
        if self.total_pages <= window:
            return list(range(1, self.total_pages + 1))
        
        # Calculate start and end of the window
        half_window = window // 2
        start = max(1, self.page - half_window)
        end = min(self.total_pages, start + window - 1)
        
        # Adjust start if we're near the end
        if end - start + 1 < window:
            start = max(1, end - window + 1)
        
        return list(range(start, end + 1))

class PaginationService:
    """Service for handling pagination logic"""
    
    # Default pagination settings
    DEFAULT_LIMIT = 25
    DEFAULT_LIMITS = [10, 25, 50, 100]
    
    @staticmethod
    def create_params(
        page: int = 1,
        limit: int = None,
        sort_by: str = "id",
        sort_order: str = "ASC",
        search_term: str = "",
        filters: Dict[str, Any] = None
    ) -> PaginationParams:
        """Create pagination parameters with defaults"""
        if limit is None:
            limit = PaginationService.DEFAULT_LIMIT
            
        return PaginationParams(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            search_term=search_term,
            filters=filters or {}
        )
    
    @staticmethod
    def build_where_clause(params: PaginationParams, search_columns: List[str] = None) -> Tuple[str, List[Any]]:
        """Build WHERE clause for SQL queries with search and filters"""
        conditions = []
        query_params = []
        
        # Add search condition
        if params.search_term and search_columns:
            search_conditions = []
            for column in search_columns:
                search_conditions.append(f"{column} LIKE %s")
                query_params.append(f"%{params.search_term}%")
            
            if search_conditions:
                conditions.append(f"({' OR '.join(search_conditions)})")
        
        # Add filter conditions
        for field, value in params.filters.items():
            if value is not None and value != "":
                if isinstance(value, list):
                    # Handle IN clauses
                    placeholders = ", ".join(["%s"] * len(value))
                    conditions.append(f"{field} IN ({placeholders})")
                    query_params.extend(value)
                else:
                    # Handle equality
                    conditions.append(f"{field} = %s")
                    query_params.append(value)
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        return where_clause, query_params
    
    @staticmethod
    def build_order_clause(params: PaginationParams, allowed_columns: List[str] = None) -> str:
        """Build ORDER BY clause for SQL queries"""
        # Validate sort column if allowed_columns is provided
        sort_by = params.sort_by
        if allowed_columns and sort_by not in allowed_columns:
            sort_by = allowed_columns[0] if allowed_columns else "id"
        
        return f"ORDER BY {sort_by} {params.sort_order}"
    
    @staticmethod
    def build_limit_clause(params: PaginationParams) -> str:
        """Build LIMIT clause for SQL queries"""
        return f"LIMIT {params.limit} OFFSET {params.offset}"
    
    @staticmethod
    def build_count_query(base_query: str) -> str:
        """Convert a SELECT query to a COUNT query"""
        # Simple approach: replace SELECT ... FROM with SELECT COUNT(*) FROM
        # This assumes the base_query starts with SELECT
        if base_query.strip().upper().startswith("SELECT"):
            # Find the FROM keyword
            from_index = base_query.upper().find(" FROM ")
            if from_index != -1:
                count_query = "SELECT COUNT(*)" + base_query[from_index:]
                
                # Remove ORDER BY and LIMIT clauses from count query
                count_query = count_query.split("ORDER BY")[0]
                count_query = count_query.split("LIMIT")[0]
                
                return count_query.strip()
        
        # Fallback: wrap the query
        return f"SELECT COUNT(*) FROM ({base_query}) as count_table"

# Example usage and defaults
PAGINATION_DEFAULTS = {
    "license_plates": {
        "limit": 25,
        "sort_by": "last_seen",
        "sort_order": "DESC",
        "search_columns": ["plate_text", "latest_location", "status"]
    },
    "detection_sessions": {
        "limit": 50,
        "sort_by": "start_time",
        "sort_order": "DESC",
        "search_columns": ["session_name", "status"]
    },
    "users": {
        "limit": 20,
        "sort_by": "username",
        "sort_order": "ASC",
        "search_columns": ["username", "role"]
    }
}

def get_pagination_defaults(table_name: str) -> Dict[str, Any]:
    """Get default pagination settings for a table"""
    return PAGINATION_DEFAULTS.get(table_name, {
        "limit": PaginationService.DEFAULT_LIMIT,
        "sort_by": "id",
        "sort_order": "ASC",
        "search_columns": []
    })
