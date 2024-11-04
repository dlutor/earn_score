from east_score import Score, tool
from encrypt import Encrypt


if __name__ == '__main__':
    import os

    encrypt_key = os.environ.get("PRIVATE_AES_KEY")
    print(encrypt_key)
    encrypt = Encrypt(encrypt_key)

    data_e = tool.read("data.txt")
    datas = encrypt.decrypt_json(data_e)

    for data in datas:
        score = Score(ct=data["ct"], ut=data["ut"])
        score.main()

