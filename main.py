from east_score import Score, tool
from encrypt import Encrypt


if __name__ == '__main__':
    import os

    encrypt_key = os.environ.get("PRIVATE_AES_KEY")
    encrypt = Encrypt(encrypt_key)

    data_e = tool.read("data.txt")
    datas = encrypt.decrypt_json(data_e)

    for i, data in enumerate(datas):
        print_key = f"账号[{i+1}/{len(datas)}]"
        score = Score(ct=data["ct"], ut=data["ut"], print_key=print_key)
        # score.print(print_key)
        score.main()

