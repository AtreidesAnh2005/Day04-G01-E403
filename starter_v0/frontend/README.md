# Research Agent Frontend (Pastel Edition)

Thư mục giao diện Web UI riêng biệt cho dự án Research Agent Tool Eval.

## Cấu trúc thư mục

```text
frontend/
├── app.py          # Ứng dụng Streamlit UI chính (Adaptive Light & Dark Purple Theme)
├── INTEGRATION.md  # Tài liệu Hợp đồng dữ liệu & Tích hợp Backend
└── README.md       # Tài liệu hướng dẫn sử dụng
```

## Tài liệu Tích hợp Backend
Xem hướng dẫn kết nối chi tiết tại [INTEGRATION.md](INTEGRATION.md).


## Hướng dẫn khởi chạy

### Cách 1: Chạy từ thư mục gốc `starter_v0`
```bash
cd starter_v0
streamlit run frontend/app.py
```

### Cách 2: Chạy từ trong thư mục `frontend`
```bash
cd starter_v0/frontend
streamlit run app.py
```

Sau khi chạy thành công, mở trình duyệt tại: `http://localhost:8501`.
