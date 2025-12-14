import qrcode


def generate_qr_code():
    qr_codes = {
        "QR1": "https://t.me/@ragamafiatest1bot?start=manager",
        "FirstDetailer": "https://t.me/@FirstDetailerBot?start=manager",
    }
    for name, url in qr_codes.items():
        qr = qrcode.make(url)
        qr.save(f"{name}.png")

#generate_qr_code()