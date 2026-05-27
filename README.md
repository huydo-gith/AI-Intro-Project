# Medical Expert Chatbot Python

Demo web app cho bài toán chatbot hỗ trợ chẩn đoán y tế dựa trên hệ chuyên gia sinh luật, với phần suy diễn viết bằng Python.

## Mục tiêu

Project mô phỏng đúng các thành phần cốt lõi của một rule-based expert system:

- `Knowledge Base`: tập facts và rules y tế.
- `Working Memory`: nơi lưu các triệu chứng người dùng đã cung cấp và các kết luận suy ra.
- `Inference Engine`: áp dụng `Forward Chaining` trên các luật dạng Horn.
- `User Interface`: giao diện chat để nhập triệu chứng và xem kết luận cùng vết suy diễn.

Hệ thống này phục vụ mục đích học tập cho các nội dung:

- Biểu diễn tri thức bằng mệnh đề và luật.
- Suy diễn trên luật `IF antecedents THEN consequent`.
- Cơ chế suy diễn tiến từ fact ban đầu tới kết luận cuối.
- Giải thích được vì sao hệ thống kết luận ra một chẩn đoán.

## Cấu trúc

- [index.html](./index.html): giao diện chính.
- [styles.css](./styles.css): giao diện chatbot và bảng giải thích.
- [app.py](./app.py): HTTP server Python và API `/api/analyze`.
- [medical_expert/knowledge_base.py](./medical_expert/knowledge_base.py): facts, rules, metadata chẩn đoán.
- [medical_expert/inference_engine.py](./medical_expert/inference_engine.py): bộ suy diễn tiến.
- [medical_expert/service.py](./medical_expert/service.py): xử lý hội thoại và nhận diện triệu chứng.
- [src/app.js](./src/app.js): frontend gọi API Python và render kết quả.

## Cách biểu diễn tri thức

Mỗi triệu chứng hay kết luận được biểu diễn thành một mệnh đề:

- `fever`
- `cough`
- `respiratory_syndrome`
- `covid19_suspected`

Luật có dạng:

```text
R11: respiratory_syndrome ∧ loss_of_taste -> covid19_suspected
R15: respiratory_alert -> urgent_medical_attention
```

Đây là mô hình phù hợp với logic mệnh đề và forward chaining vì:

- antecedents là tập fact cần thỏa.
- consequent là fact mới được thêm vào working memory.
- quá trình lặp tiếp tục cho tới khi không còn luật nào kích hoạt thêm được.

## Luồng suy diễn

1. Người dùng nhập triệu chứng qua chat hoặc bấm symptom chip.
2. Hệ thống ánh xạ câu tự nhiên sang facts.
3. Các facts ban đầu được đưa vào `working memory`.
4. `ForwardChainingEngine` duyệt toàn bộ rule base.
5. Nếu toàn bộ antecedents của một luật đều đúng, consequent được thêm vào bộ nhớ.
6. Hệ thống lưu lại `trace` để giải thích các luật đã kích hoạt.
7. Khi xuất hiện fact loại `diagnosis`, chatbot trả về kết luận tạm thời và khuyến nghị.

## Chạy project bằng Python

```powershell
python app.py
```

Sau đó mở `http://127.0.0.1:8000`.

## Mở rộng tiếp theo

- Bổ sung nhiều luật và nhiều bệnh hơn từ tri thức chuyên gia.
- Thêm độ tin cậy hoặc certainty factor.
- Tách tầng `question selection` để chatbot hỏi triệu chứng tiếp theo thông minh hơn.
- Lưu session hội thoại.
- Kết nối backend để quản lý rule base bằng JSON hoặc database.

## Lưu ý học thuật

Project được xây theo tinh thần của mô hình hệ chuyên gia y tế rule-based trong các tài liệu bạn cung cấp:

- tri thức được tổ chức thành facts và rules,
- suy diễn theo luật tiến,
- có bộ nhớ làm việc,
- có thể giải thích chuỗi suy luận.

Nó không phải hệ thống chẩn đoán lâm sàng thực tế và không nên dùng thay thế tư vấn y khoa chuyên môn.
