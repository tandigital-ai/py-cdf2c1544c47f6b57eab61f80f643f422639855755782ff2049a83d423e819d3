# TAX INVOICE PRO v1.0.0

Ứng dụng desktop Windows chạy hoàn toàn offline, dùng để tra cứu – xem – lưu trữ –
xuất hóa đơn điện tử đã có sẵn trên máy.

Tác giả: **TDA** — Điện thoại: **0986509106**

## 1. Yêu cầu

- Python 3.11

## 2. Tạo môi trường ảo

Windows (PowerShell hoặc CMD):

```bat
cd duong_dan_den_thu_muc_du_an
py -3.11 -m venv .venv
.venv\Scripts\activate
```

## 3. Cài thư viện

```bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Chạy ứng dụng

```bat
python app.py
```

Thoát môi trường ảo:

```bat
deactivate
```