Tiện ích Muse2API - Hướng dẫn cài đặt
====================================

Tiện ích này giúp đồng bộ Cookie đăng nhập của muse.ai từ trình duyệt của bạn vào dịch vụ muse2api một cách dễ dàng và nhanh chóng, không cần cài đặt Python hay mở terminal.


1. Giải nén
-----------
Giải nén tệp muse2api-extension.zip vào một thư mục cố định trên máy tính, ví dụ:

    Windows : D:\muse2api-extension
    macOS   : ~/Documents/muse2api-extension

Sau khi giải nén, bạn sẽ thấy các tệp: manifest.json, popup.html, popup.js.


2. Cài đặt vào Chrome / Edge
----------------------------
Trên Google Chrome:
  1. Nhập vào thanh địa chỉ: chrome://extensions rồi nhấn Enter
  2. Bật công tắc "Chế độ cho nhà phát triển" (Developer mode) ở góc trên bên phải
  3. Nhấn vào nút "Tải tiện ích đã giải nén" (Load unpacked) ở góc trên bên trái
  4. Chọn thư mục mà bạn vừa giải nén ở bước 1 (chọn cả thư mục)
  5. Biểu tượng tiện ích sẽ xuất hiện trên thanh công cụ trình duyệt (nên ghim tiện ích để tiện dùng)

Trên Microsoft Edge:
  1. Nhập vào thanh địa chỉ: edge://extensions rồi nhấn Enter
  2. Bật công tắc "Chế độ nhà phát triển" (Developer mode) ở thanh bên trái
  3. Nhấn "Tải gói mở rộng chưa giải nén" (Load unpacked)
  4. Các bước tiếp theo tương tự Chrome

Các trình duyệt nhân Chromium khác (Brave, Cốc Cốc, Opera...) thực hiện tương tự.


3. Hướng dẫn sử dụng
--------------------
1. Mở trình duyệt, truy cập https://muse.ai/ và đăng nhập cho đến khi thấy màn hình chat.
2. Mở trang quản trị muse2api (tab "Kho tài khoản"), sao chép BASE URL và API Key.
3. Nhấn vào biểu tượng tiện ích Muse2API trên thanh công cụ, điền BASE URL và API Key (chỉ cần điền một lần, tiện ích sẽ tự ghi nhớ).
4. Nhấn "Đọc & Nhập Cookie". Khi thấy thông báo "✓ Nhập thành công" là hoàn tất.


4. Câu hỏi thường gặp
---------------------
H: Báo lỗi "Không đọc được Cookie của muse.ai"
Đ: Trình duyệt này chưa đăng nhập muse.ai. Hãy mở https://muse.ai/ và đăng nhập trước.

H: Báo lỗi "Thiếu các mục cốt lõi hatch_sess..."
Đ: Phiên đăng nhập chưa tải xong hoặc chưa vào tới giao diện chat. Vui lòng mở https://muse.ai/, tải lại trang và thử lại.
