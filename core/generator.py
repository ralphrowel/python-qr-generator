import qrcode

def generate_qr(data, filename="qr_code.png"):

    qr = qrcode.make(data)

    qr.save(filename)

    return filename