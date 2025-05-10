import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class DatabaseEncryption:
    """Simple database file encryption using Fernet symmetric encryption"""
    
    @staticmethod
    def generate_key(password, salt=None):
        """Generate an encryption key from a password"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    @staticmethod
    def encrypt_file(file_path, password):
        """Encrypt a file using a password"""
        try:
            # Generate key and salt
            key, salt = DatabaseEncryption.generate_key(password)
            
            # Read the file
            with open(file_path, 'rb') as file:
                data = file.read()
            
            # Encrypt the data
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data)
            
            # Create encrypted file name
            encrypted_file = f"{file_path}.enc"
            
            # Write the encrypted data
            with open(encrypted_file, 'wb') as file:
                # First write the salt
                file.write(salt)
                # Then write the encrypted data
                file.write(encrypted_data)
            
            logging.info(f"File encrypted: {file_path}")
            return encrypted_file
            
        except Exception as e:
            logging.error(f"Encryption error: {e}")
            raise
    
    @staticmethod
    def decrypt_file(encrypted_file, password, output_file=None):
        """Decrypt a file using a password"""
        try:
            # Read the encrypted file
            with open(encrypted_file, 'rb') as file:
                # First 16 bytes are the salt
                salt = file.read(16)
                # Rest is the encrypted data
                encrypted_data = file.read()
            
            # Generate key with the stored salt
            key, _ = DatabaseEncryption.generate_key(password, salt)
            
            # Decrypt the data
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Determine output file path
            if output_file is None:
                # Remove .enc extension if present
                if encrypted_file.endswith('.enc'):
                    output_file = encrypted_file[:-4]
                else:
                    output_file = f"{encrypted_file}.dec"
            
            # Write the decrypted data
            with open(output_file, 'wb') as file:
                file.write(decrypted_data)
            
            logging.info(f"File decrypted: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Decryption error: {e}")
            raise