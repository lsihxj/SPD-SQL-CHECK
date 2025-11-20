"""
加密工具类
用于API密钥和数据库密码的加密存储
"""
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """加密服务类"""
    
    def __init__(self, encryption_key: str):
        """
        初始化加密服务
        
        Args:
            encryption_key: 加密密钥（至少32字符）
        """
        if len(encryption_key) < 32:
            raise ValueError("Encryption key must be at least 32 characters long")
        
        # 使用PBKDF2从密钥生成Fernet密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'sql_check_tool_salt',  # 在生产环境中应该使用随机salt
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, plain_text: str) -> str:
        """
        加密文本
        
        Args:
            plain_text: 明文
            
        Returns:
            加密后的文本（Base64编码）
        """
        if not plain_text:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(plain_text.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        解密文本
        
        Args:
            encrypted_text: 加密的文本（Base64编码）
            
        Returns:
            解密后的明文
        """
        if not encrypted_text:
            return ""
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt: {str(e)}")
    
    def encrypt_if_needed(self, text: str, already_encrypted: bool = False) -> str:
        """
        如果文本未加密则加密
        
        Args:
            text: 文本
            already_encrypted: 是否已经加密
            
        Returns:
            加密后的文本
        """
        if already_encrypted or not text:
            return text
        return self.encrypt(text)


# 全局加密服务实例（将在应用启动时初始化）
_encryption_service: EncryptionService | None = None


def init_encryption_service(encryption_key: str):
    """
    初始化全局加密服务
    
    Args:
        encryption_key: 加密密钥
    """
    global _encryption_service
    _encryption_service = EncryptionService(encryption_key)


def get_encryption_service() -> EncryptionService:
    """
    获取全局加密服务实例
    
    Returns:
        EncryptionService实例
    """
    if _encryption_service is None:
        raise RuntimeError("Encryption service not initialized. Call init_encryption_service first.")
    return _encryption_service
