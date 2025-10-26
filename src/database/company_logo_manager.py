"""
Company Logo Manager - Database operations for storing and retrieving company logos
"""
import base64
from datetime import datetime
from bson import ObjectId


class CompanyLogoManager:
    """Manages company logos in MongoDB"""

    def __init__(self, mongo_adapter):
        """
        Initialize the logo manager

        Args:
            mongo_adapter: MongoAdapter instance for database operations
        """
        self.db = mongo_adapter
        self.collection_name = 'company_logos'

    def save_logo(self, logo_name, logo_path, logo_data_base64):
        """
        Save a company logo to the database

        Args:
            logo_name: Name/description of the logo
            logo_path: Original file path (for reference)
            logo_data_base64: Base64 encoded image data

        Returns:
            str: ID of the saved logo or None if failed
        """
        try:
            logo_document = {
                'logo_name': logo_name,
                'logo_path': logo_path,
                'logo_data': logo_data_base64,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            # Check if logo with same name exists
            existing = self.db.db[self.collection_name].find_one({'logo_name': logo_name})

            if existing:
                # Update existing logo
                self.db.db[self.collection_name].update_one(
                    {'_id': existing['_id']},
                    {'$set': {
                        'logo_data': logo_data_base64,
                        'logo_path': logo_path,
                        'updated_at': datetime.now()
                    }}
                )
                return str(existing['_id'])
            else:
                # Insert new logo
                result = self.db.db[self.collection_name].insert_one(logo_document)
                return str(result.inserted_id)

        except Exception as e:
            print(f"Error saving logo: {e}")
            return None

    def get_logo(self, logo_id):
        """
        Get a logo by ID

        Args:
            logo_id: Logo ID (string or ObjectId)

        Returns:
            dict: Logo document or None if not found
        """
        try:
            if isinstance(logo_id, str):
                logo_id = ObjectId(logo_id)

            logo = self.db.db[self.collection_name].find_one({'_id': logo_id})
            if logo:
                logo['_id'] = str(logo['_id'])
            return logo

        except Exception as e:
            print(f"Error getting logo: {e}")
            return None

    def get_logo_by_name(self, logo_name):
        """
        Get a logo by name

        Args:
            logo_name: Name of the logo

        Returns:
            dict: Logo document or None if not found
        """
        try:
            logo = self.db.db[self.collection_name].find_one({'logo_name': logo_name})
            if logo:
                logo['_id'] = str(logo['_id'])
            return logo

        except Exception as e:
            print(f"Error getting logo by name: {e}")
            return None

    def get_all_logos(self):
        """
        Get all logos from the database

        Returns:
            list: List of logo documents
        """
        try:
            logos = list(self.db.db[self.collection_name].find())
            for logo in logos:
                logo['_id'] = str(logo['_id'])
            return logos

        except Exception as e:
            print(f"Error getting all logos: {e}")
            return []

    def get_logo_names(self):
        """
        Get all logo names for dropdown population

        Returns:
            list: List of logo names
        """
        try:
            logos = self.db.db[self.collection_name].find({}, {'logo_name': 1})
            return [logo['logo_name'] for logo in logos]

        except Exception as e:
            print(f"Error getting logo names: {e}")
            return []

    def delete_logo(self, logo_id):
        """
        Delete a logo by ID

        Args:
            logo_id: Logo ID (string or ObjectId)

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            if isinstance(logo_id, str):
                logo_id = ObjectId(logo_id)

            result = self.db.db[self.collection_name].delete_one({'_id': logo_id})
            return result.deleted_count > 0

        except Exception as e:
            print(f"Error deleting logo: {e}")
            return False

    def delete_logo_by_name(self, logo_name):
        """
        Delete a logo by name

        Args:
            logo_name: Name of the logo

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            result = self.db.db[self.collection_name].delete_one({'logo_name': logo_name})
            return result.deleted_count > 0

        except Exception as e:
            print(f"Error deleting logo by name: {e}")
            return False
