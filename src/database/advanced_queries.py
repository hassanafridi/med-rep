# src/database/advanced_queries.py

"""
Advanced MongoDB queries for enhanced analytics and reporting
These queries leverage MongoDB's aggregation framework for powerful data analysis
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AdvancedQueries:
    def __init__(self, mongo_db):
        self.db = mongo_db.db
    
    def get_top_customers_by_revenue(self, limit: int = 10) -> List[Dict]:
        """Get top customers by total revenue"""
        pipeline = [
            {
                "$lookup": {
                    "from": "entries",
                    "localField": "_id",
                    "foreignField": "customer_id",
                    "as": "entries"
                }
            },
            {
                "$addFields": {
                    "total_revenue": {
                        "$sum": {
                            "$map": {
                                "input": "$entries",
                                "as": "entry",
                                "in": {
                                    "$multiply": ["$$entry.quantity", "$$entry.unit_price"]
                                }
                            }
                        }
                    }
                }
            },
            {
                "$sort": {"total_revenue": -1}
            },
            {
                "$limit": limit
            },
            {
                "$project": {
                    "name": 1,
                    "contact": 1,
                    "total_revenue": 1,
                    "entry_count": {"$size": "$entries"}
                }
            }
        ]
        
        try:
            return list(self.db.customers.aggregate(pipeline))
        except Exception as e:
            logger.error(f"Error getting top customers: {e}")
            return []
    
    def get_product_performance_analysis(self) -> List[Dict]:
        """Analyze product performance with detailed metrics"""
        pipeline = [
            {
                "$lookup": {
                    "from": "entries",
                    "localField": "_id",
                    "foreignField": "product_id",
                    "as": "entries"
                }
            },
            {
                "$addFields": {
                    "total_quantity_sold": {"$sum": "$entries.quantity"},
                    "total_revenue": {
                        "$sum": {
                            "$map": {
                                "input": "$entries",
                                "as": "entry",
                                "in": {"$multiply": ["$$entry.quantity", "$$entry.unit_price"]}
                            }
                        }
                    },
                    "unique_customers": {
                        "$size": {
                            "$setUnion": "$entries.customer_id"
                        }
                    },
                    "avg_order_size": {
                        "$cond": {
                            "if": {"$gt": [{"$size": "$entries"}, 0]},
                            "then": {
                                "$avg": "$entries.quantity"
                            },
                            "else": 0
                        }
                    }
                }
            },
            {
                "$sort": {"total_revenue": -1}
            },
            {
                "$project": {
                    "name": 1,
                    "description": 1,
                    "unit_price": 1,
                    "batch_number": 1,
                    "expiry_date": 1,
                    "total_quantity_sold": 1,
                    "total_revenue": 1,
                    "unique_customers": 1,
                    "avg_order_size": 1,
                    "revenue_per_customer": {
                        "$cond": {
                            "if": {"$gt": ["$unique_customers", 0]},
                            "then": {"$divide": ["$total_revenue", "$unique_customers"]},
                            "else": 0
                        }
                    }
                }
            }
        ]
        
        try:
            return list(self.db.products.aggregate(pipeline))
        except Exception as e:
            logger.error(f"Error analyzing product performance: {e}")
            return []
    
    def get_monthly_sales_trend(self, months: int = 12) -> List[Dict]:
        """Get monthly sales trend for the specified number of months"""
        start_date = datetime.now() - timedelta(days=months * 30)
        
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$lookup": {
                    "from": "products",
                    "localField": "product_id",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {
                "$unwind": "$product"
            },
            {
                "$addFields": {
                    "revenue": {"$multiply": ["$quantity", "$unit_price"]},
                    "month_year": {
                        "$dateToString": {
                            "format": "%Y-%m",
                            "date": "$created_at"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$month_year",
                    "total_revenue": {"$sum": "$revenue"},
                    "total_quantity": {"$sum": "$quantity"},
                    "unique_customers": {"$addToSet": "$customer_id"},
                    "unique_products": {"$addToSet": "$product_id"},
                    "entry_count": {"$sum": 1}
                }
            },
            {
                "$addFields": {
                    "customer_count": {"$size": "$unique_customers"},
                    "product_count": {"$size": "$unique_products"}
                }
            },
            {
                "$sort": {"_id": 1}
            },
            {
                "$project": {
                    "month": "$_id",
                    "total_revenue": 1,
                    "total_quantity": 1,
                    "customer_count": 1,
                    "product_count": 1,
                    "entry_count": 1,
                    "avg_order_value": {
                        "$cond": {
                            "if": {"$gt": ["$entry_count", 0]},
                            "then": {"$divide": ["$total_revenue", "$entry_count"]},
                            "else": 0
                        }
                    }
                }
            }
        ]
        
        try:
            return list(self.db.entries.aggregate(pipeline))
        except Exception as e:
            logger.error(f"Error getting sales trend: {e}")
            return []
    
    def get_customer_segmentation(self) -> Dict[str, List[Dict]]:
        """Segment customers based on purchase behavior"""
        pipeline = [
            {
                "$lookup": {
                    "from": "entries",
                    "localField": "_id",
                    "foreignField": "customer_id",
                    "as": "entries"
                }
            },
            {
                "$addFields": {
                    "total_spent": {
                        "$sum": {
                            "$map": {
                                "input": "$entries",
                                "as": "entry",
                                "in": {"$multiply": ["$$entry.quantity", "$$entry.unit_price"]}
                            }
                        }
                    },
                    "order_count": {"$size": "$entries"},
                    "last_order_date": {"$max": "$entries.created_at"}
                }
            },
            {
                "$addFields": {
                    "avg_order_value": {
                        "$cond": {
                            "if": {"$gt": ["$order_count", 0]},
                            "then": {"$divide": ["$total_spent", "$order_count"]},
                            "else": 0
                        }
                    },
                    "days_since_last_order": {
                        "$cond": {
                            "if": {"$ne": ["$last_order_date", None]},
                            "then": {
                                "$divide": [
                                    {"$subtract": [datetime.now(), "$last_order_date"]},
                                    1000 * 60 * 60 * 24  # Convert to days
                                ]
                            },
                            "else": 999
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "segment": {
                        "$switch": {
                            "branches": [
                                {
                                    "case": {
                                        "$and": [
                                            {"$gte": ["$total_spent", 10000]},
                                            {"$lte": ["$days_since_last_order", 30]}
                                        ]
                                    },
                                    "then": "VIP"
                                },
                                {
                                    "case": {
                                        "$and": [
                                            {"$gte": ["$total_spent", 5000]},
                                            {"$lte": ["$days_since_last_order", 60]}
                                        ]
                                    },
                                    "then": "High Value"
                                },
                                {
                                    "case": {
                                        "$and": [
                                            {"$gte": ["$order_count", 5]},
                                            {"$lte": ["$days_since_last_order", 90]}
                                        ]
                                    },
                                    "then": "Regular"
                                },
                                {
                                    "case": {"$gt": ["$days_since_last_order", 90]},
                                    "then": "Inactive"
                                }
                            ],
                            "default": "New"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$segment",
                    "customers": {
                        "$push": {
                            "name": "$name",
                            "contact": "$contact",
                            "total_spent": "$total_spent",
                            "order_count": "$order_count",
                            "avg_order_value": "$avg_order_value",
                            "days_since_last_order": "$days_since_last_order"
                        }
                    },
                    "count": {"$sum": 1},
                    "total_revenue": {"$sum": "$total_spent"}
                }
            }
        ]
        
        try:
            results = list(self.db.customers.aggregate(pipeline))
            return {segment["_id"]: segment for segment in results}
        except Exception as e:
            logger.error(f"Error segmenting customers: {e}")
            return {}
    
    def get_expiring_products(self, days_ahead: int = 30) -> List[Dict]:
        """Get products expiring within specified days"""
        expiry_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        try:
            pipeline = [
                {
                    "$match": {
                        "expiry_date": {
                            "$lte": expiry_date,
                            "$ne": ""
                        }
                    }
                },
                {
                    "$lookup": {
                        "from": "entries",
                        "localField": "_id",
                        "foreignField": "product_id",
                        "as": "recent_entries"
                    }
                },
                {
                    "$addFields": {
                        "stock_movement": {"$size": "$recent_entries"},
                        "days_to_expiry": {
                            "$divide": [
                                {"$subtract": [
                                    {"$dateFromString": {"dateString": "$expiry_date"}},
                                    datetime.now()
                                ]},
                                1000 * 60 * 60 * 24
                            ]
                        }
                    }
                },
                {
                    "$sort": {"days_to_expiry": 1}
                },
                {
                    "$project": {
                        "name": 1,
                        "batch_number": 1,
                        "expiry_date": 1,
                        "unit_price": 1,
                        "days_to_expiry": {"$round": ["$days_to_expiry", 0]},
                        "stock_movement": 1
                    }
                }
            ]
            
            return list(self.db.products.aggregate(pipeline))
        except Exception as e:
            logger.error(f"Error getting expiring products: {e}")
            return []
    
    def get_credit_debit_analysis(self) -> Dict[str, Any]:
        """Analyze credit vs debit transactions"""
        pipeline = [
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "customer_id",
                    "foreignField": "_id",
                    "as": "customer"
                }
            },
            {
                "$unwind": "$customer"
            },
            {
                "$addFields": {
                    "transaction_value": {"$multiply": ["$quantity", "$unit_price"]}
                }
            },
            {
                "$group": {
                    "_id": {
                        "customer_id": "$customer_id",
                        "customer_name": "$customer.name",
                        "is_credit": "$is_credit"
                    },
                    "total_amount": {"$sum": "$transaction_value"},
                    "transaction_count": {"$sum": 1}
                }
            },
            {
                "$group": {
                    "_id": {
                        "customer_id": "$_id.customer_id",
                        "customer_name": "$_id.customer_name"
                    },
                    "transactions": {
                        "$push": {
                            "type": {"$cond": ["$_id.is_credit", "Credit", "Debit"]},
                            "total_amount": "$total_amount",
                            "count": "$transaction_count"
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "credit_total": {
                        "$sum": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$transactions",
                                        "as": "txn",
                                        "cond": {"$eq": ["$$txn.type", "Credit"]}
                                    }
                                },
                                "as": "credit",
                                "in": "$$credit.total_amount"
                            }
                        }
                    },
                    "debit_total": {
                        "$sum": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$transactions",
                                        "as": "txn",
                                        "cond": {"$eq": ["$$txn.type", "Debit"]}
                                    }
                                },
                                "as": "debit",
                                "in": "$$debit.total_amount"
                            }
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "balance": {"$subtract": ["$credit_total", "$debit_total"]}
                }
            },
            {
                "$project": {
                    "customer_name": "$_id.customer_name",
                    "credit_total": 1,
                    "debit_total": 1,
                    "balance": 1,
                    "status": {
                        "$cond": {
                            "if": {"$gt": ["$balance", 0]},
                            "then": "Credit Balance",
                            "else": {
                                "$cond": {
                                    "if": {"$lt": ["$balance", 0]},
                                    "then": "Debit Balance",
                                    "else": "Balanced"
                                }
                            }
                        }
                    }
                }
            },
            {
                "$sort": {"balance": -1}
            }
        ]
        
        try:
            customer_balances = list(self.db.entries.aggregate(pipeline))
            
            # Summary statistics
            summary_pipeline = [
                {
                    "$addFields": {
                        "transaction_value": {"$multiply": ["$quantity", "$unit_price"]}
                    }
                },
                {
                    "$group": {
                        "_id": "$is_credit",
                        "total_amount": {"$sum": "$transaction_value"},
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            summary = list(self.db.entries.aggregate(summary_pipeline))
            
            return {
                "customer_balances": customer_balances,
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Error analyzing credit/debit: {e}")
            return {"customer_balances": [], "summary": []}
    
    def get_sales_forecasting_data(self) -> Dict[str, Any]:
        """Get data for sales forecasting based on historical trends"""
        pipeline = [
            {
                "$addFields": {
                    "revenue": {"$multiply": ["$quantity", "$unit_price"]},
                    "week_of_year": {"$week": "$created_at"},
                    "year": {"$year": "$created_at"}
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": "$year",
                        "week": "$week_of_year",
                        "product_id": "$product_id"
                    },
                    "weekly_revenue": {"$sum": "$revenue"},
                    "weekly_quantity": {"$sum": "$quantity"}
                }
            },
            {
                "$lookup": {
                    "from": "products",
                    "localField": "_id.product_id",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {
                "$unwind": "$product"
            },
            {
                "$project": {
                    "year": "$_id.year",
                    "week": "$_id.week",
                    "product_name": "$product.name",
                    "weekly_revenue": 1,
                    "weekly_quantity": 1
                }
            },
            {
                "$sort": {"year": 1, "week": 1}
            }
        ]
        
        try:
            return list(self.db.entries.aggregate(pipeline))
        except Exception as e:
            logger.error(f"Error getting forecasting data: {e}")
            return []