from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64, json


class Encrypt:
    def __init__(self, key, iv=""):
        self.key = key.encode('utf-8')
        self.iv = iv.encode('utf-8')

    # @staticmethod
    def pkcs7padding(self, text):
        """明文使用PKCS7填充 """
        bs = 16
        length = len(text)
        bytes_length = len(text.encode('utf-8'))
        padding_size = length if (bytes_length == length) else bytes_length
        padding = bs - padding_size % bs
        padding_text = chr(padding) * padding
        self.coding = chr(padding)
        return text + padding_text

    def aes_encrypt(self, content):
        """ AES加密 """
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        # 处理明文
        content_padding = self.pkcs7padding(content)
        # 加密
        encrypt_bytes = cipher.encrypt(content_padding.encode('utf-8'))
        # 重新编码
        result = str(base64.b64encode(encrypt_bytes), encoding='utf-8')
        return result

    def aes_decrypt(self, content):
        """AES解密 """
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        content = base64.b64decode(content)
        text = cipher.decrypt(content).decode('utf-8')
        return text.rstrip(self.coding)

    def encrypt_aes_ecb(self, plain_str, ):
        """
        无偏移的AES加密
        :param plain_str: 需要加密的明文
        :param key: AES私钥
        :return: base64后的密文
        """
        cipher = AES.new(self.key, AES.MODE_ECB)
        ciphertext = cipher.encrypt(pad(plain_str.encode(), AES.block_size))
        return base64.b64encode(ciphertext).decode()


    def decrypt_aes_ecb(self, ciphertext):
        """
        无偏移的AES解密
        :param ciphertext: 需要解密的密文
        :param key: AES私钥
        :return: 解密后的明文
        """
        ciphertext = base64.b64decode(ciphertext)
        cipher = AES.new(self.key, AES.MODE_ECB)
        plain_str = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return plain_str.decode()

    def encrypt(self, text):
        if self.iv == b"":
            return self.encrypt_aes_ecb(text)
        else:
            return self.aes_encrypt(text)

    def decrypt(self, text):
        if self.iv == b"":
            return self.decrypt_aes_ecb(text)
        else:
            return self.aes_decrypt(text)

    def encrypt_json(self, data):
        return self.encrypt(json.dumps(data))

    def decrypt_json(self, data):
        return json.loads(self.decrypt(data))


if __name__ == '__main__':
    import json
    key = 'ONxYDyNaCoyTzsp83JoQ3YYuMPHxk3j7'
    # iv = 'yNaCoyTzsp83JoQ3'
    iv = ""

#     ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    p_json = {
        "CompanyName": "testmall",
        "UserId": "test",
        "Password": "grasp@101",
        "TimeStamp": "2019-05-05 10:59:26"
    }

    a = Encrypt(key=key, iv=iv)
    # e = a.aes_encrypt(json.dumps(p_json))
    # d = json.loads(a.aes_decrypt(e))
    # e = a.encrypt_aes_ecb(json.dumps(p_json))
    # d = json.loads(a.decrypt_aes_ecb(e))
    e = a.encrypt_json(p_json)
    d = a.decrypt_json(e)
    print("加密:", e)
    print("解密:", d)
    with open("data.txt", 'w') as f:
        f.write(e)
