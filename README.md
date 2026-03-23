# Phân hoạch các số

Dự án này trình bày, chuẩn hóa và benchmark các chiến lược thiết kế giải thuật
cho bài toán phân hoạch mảng số thực khác `0`, với giao diện đồ họa phát triển
trên `Tkinter` và cơ chế lưu vết kết quả phục vụ đối chiếu runtime trên cùng
một điều kiện dữ liệu đầu vào.

## Giới thiệu

Bài toán đặt ra yêu cầu sắp xếp lại một mảng `A` sao cho toàn bộ số âm nằm ở
phía trái và toàn bộ số dương nằm ở phía phải. Giá trị trả về của thuật toán là
`k`, tương ứng với số phần tử âm trong mảng.

Điều kiện hậu kiểm được chuẩn hóa thống nhất cho toàn hệ thống:

- `A[:k]` chỉ chứa số âm
- `A[k:]` chỉ chứa số dương

Trên cơ sở đó, repo được tổ chức theo ba mục tiêu chính:

- thống nhất public API giữa các thuật toán
- tập trung metadata học thuật tại một nguồn dùng chung cho UI, benchmark và lịch sử chạy
- duy trì khả năng quan sát trực quan thông qua giao diện Tkinter và biểu đồ runtime

## Phạm vi học thuật

Repo hiện duy trì bốn chiến lược chính thức, tương ứng với các cách tiếp cận phù
hợp nhất cho bài toán trong bối cảnh môn học và thực hành phân tích giải thuật.

| Thuật toán | Public function | Chiến lược | Time | Space | In-place | Stable | Deterministic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Direct Scan | `partition_direct_scan(A)` | Direct / Straightforward Method | `O(n^2)` | `O(1)` | Có | Không | Có |
| Two Pointers | `partition_two_pointers(A)` | Direct Optimized / In-place Partition | `O(n)` | `O(1)` | Có | Không | Có |
| Transform-and-Conquer | `partition_transform_and_conquer(A)` | Transform-and-Conquer | `O(n)` | `O(n)` | Không | Có | Có |
| Divide-and-Conquer | `partition_divide_and_conquer(A)` | Divide-and-Conquer | `O(n log n)` | `O(n)` | Không | Có | Có |

Metadata học thuật của toàn bộ tập thuật toán được tập trung trong
[`algorithms/__init__.py`](./algorithms/__init__.py). Cách tổ chức này giúp hạn
chế sai lệch giữa tên hiển thị, mô tả chiến lược, complexity và hành vi thực tế
khi dữ liệu được đi qua nhiều lớp của ứng dụng.

## Giao diện và khả năng quan sát

Ứng dụng cung cấp hai không gian làm việc chính:

- khu chạy benchmark: cấu hình dữ liệu, chạy một thuật toán hoặc benchmark toàn
  bộ tập thuật toán chính thức, quan sát bảng tổng kết và demo trực quan theo
  từng lần chạy
- khu plot lịch sử: tổng hợp runtime trung bình theo kích thước đầu vào, hỗ trợ
  lọc theo dataset, batch, trạng thái log-scale và tương tác hover trên từng
  điểm dữ liệu

Các thành phần trực quan chính bao gồm:

- preview dataset trước khi thực thi
- bảng tổng kết các lần run trong cùng một ngữ cảnh benchmark
- demo before/after gắn với dòng đang chọn
- biểu đồ lịch sử runtime trung bình theo `n`
- lưu vết `results.csv` và dữ liệu JSON phục vụ debug khi cần

## Kiến trúc mã nguồn

```text
.
├── algorithms/
│   ├── __init__.py
│   ├── direct_scan.py
│   ├── two_pointers.py
│   ├── transform_and_conquer.py
│   └── divide_and_conquer.py
├── core/
├── history/
├── ui/
├── outputs/
├── app.py
├── main.py
└── requirements.txt
```

Vai trò của từng khối chính:

- `algorithms/`: thuật toán, metadata và public API chính thức
- `core/`: generator, validation, model dữ liệu và tiện ích nền tảng
- `history/`: lưu kết quả benchmark, chuẩn hóa record và đọc lịch sử
- `ui/`: giao diện Tkinter cho chạy benchmark và hiển thị plot
- `outputs/`: đầu ra thực nghiệm, bao gồm CSV lịch sử và JSON debug

## Môi trường thực thi

Môi trường mục tiêu của dự án gồm:

- Python `3.9+`
- `Tkinter`
- `matplotlib`

`Tkinter` không được khai báo trong `requirements.txt` vì đây không phải
package `pip` theo mô hình thông thường. Trên Windows và macOS, `Tkinter`
thường đi kèm Python chính thức. Trên một số bản phân phối Linux, thành phần
này cần được cài đặt thông qua package manager của hệ điều hành, ví dụ:

```bash
sudo apt install python3-tk
```

## Thiết lập môi trường

Việc cô lập môi trường được khuyến nghị thông qua `venv`.

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux / Git Bash

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Vận hành ứng dụng

Điểm vào mặc định của ứng dụng:

```bash
python main.py
```

Module giao diện chính cũng có thể được gọi trực tiếp:

```bash
python app.py
```

Sau khi khởi động, luồng sử dụng chuẩn của hệ thống gồm ba bước:

1. cấu hình `n`, `seed`, tỷ lệ âm và số lần chạy
2. preview dataset hoặc thực thi benchmark
3. quan sát bảng tổng kết, demo trực quan và biểu đồ lịch sử

## Chuẩn dữ liệu và validation

Generator tạo mảng số nguyên hoặc số thực khác `0` theo `seed` xác định, phục
vụ benchmark lặp lại trên cùng một dataset. Public API của các thuật toán có
lớp validation đầu vào nhằm từ chối mảng chứa `0`, qua đó giữ nguyên phát biểu
gốc của bài toán và tránh các trường hợp biên không còn ý nghĩa học thuật rõ
ràng.

## Dữ liệu đầu ra

Kết quả benchmark được lưu trong thư mục `outputs/`:

- `results.csv`: nhật ký các lần chạy
- `arrays/*.json`: ảnh chụp mảng đầu ra trong những trường hợp cần lưu debug

Mỗi record lưu các thông tin trọng yếu như:

- thuật toán
- `n`
- `seed`
- tỷ lệ âm
- runtime trung bình
- `k`
- trạng thái `partition_ok`
- trạng thái `k_ok`
- trạng thái tổng `ok`

## Ghi chú triển khai

- Tất cả thuật toán tuân theo cùng một interface trả về `k` và thao tác trực
  tiếp trên mảng đầu vào.
- `Transform-and-Conquer` và `Divide-and-Conquer` sử dụng bộ nhớ phụ nhưng ghi
  kết quả trở lại `A` trước khi kết thúc.
- UI, benchmark runner và history layer dùng chung một nguồn metadata học
  thuật, nhờ đó tránh lệch tên thuật toán hoặc lệch complexity giữa các module.
- Hệ thống plot chỉ tổng hợp các mẫu hợp lệ và hỗ trợ lọc theo dataset hoặc
  batch, bảo toàn khả năng đối chiếu runtime trong cùng điều kiện dữ liệu.

## Ghi chú vận hành

Trong trường hợp interpreter Python không đi kèm `Tkinter` đầy đủ, ứng dụng có
thể không khởi động được dù phần mã Python và dependencies đã đúng. Khi đó,
việc kiểm tra cài đặt `Tcl/Tk` của môi trường Python đang sử dụng là cần thiết.

`requirements.txt` hiện chỉ bao gồm dependency ngoài standard library:

```text
matplotlib>=3.8,<4.0
```
