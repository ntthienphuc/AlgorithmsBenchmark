# Partition Numbers Benchmark Studio

Ứng dụng Python + Tkinter để minh họa và benchmark bài toán:

> Cho mảng `A` gồm các số thực hoặc số nguyên khác `0`, hãy sắp xếp lại để mọi số âm nằm bên trái, mọi số dương nằm bên phải. Hàm trả về `k = số phần tử âm`.

Project này phù hợp để:

- học và so sánh các chiến lược thiết kế giải thuật
- benchmark nhiều thuật toán trên cùng một base array
- trực quan hóa kết quả bằng GUI Tkinter và biểu đồ lịch sử runtime

## Tính năng chính

- GUI Tkinter để preview dataset, chạy từng thuật toán, hoặc benchmark toàn bộ
- bảng tổng kết + demo trực quan `Before / After`
- plot lịch sử runtime trung bình theo kích thước `n`
- metadata học thuật tập trung cho từng thuật toán
- validate input công khai: reject mảng chứa `0`
- lưu lịch sử chạy vào `outputs/results.csv` và JSON debug khi cần

## 4 thuật toán chính thức

| Display name | Public function | Strategy | Time | Space | In-place | Stable | Deterministic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Direct Scan | `partition_direct_scan(A)` | Direct / Straightforward Method | `O(n^2)` | `O(1)` | Yes | No | Yes |
| Two Pointers | `partition_two_pointers(A)` | Direct Optimized / In-place Partition | `O(n)` | `O(1)` | Yes | No | Yes |
| Transform-and-Conquer | `partition_transform_and_conquer(A)` | Transform-and-Conquer | `O(n)` | `O(n)` | No | Yes | Yes |
| Divide-and-Conquer | `partition_divide_and_conquer(A)` | Divide-and-Conquer | `O(n log n)` | `O(n)` | No | Yes | Yes |

Ghi chú:

- `Transform-and-Conquer` và `Divide-and-Conquer` dùng bộ nhớ phụ rồi chép kết quả trở lại `A`.

## Các chiến lược đã loại khỏi public API

Ba biến thể sau không còn được export chính thức:

- dynamic programming
- branch and bound
- backtracking

Lý do: chúng có thể cho đầu ra đúng, nhưng không đúng tinh thần chiến lược thiết kế giải thuật phù hợp nhất cho bài toán phân hoạch theo dấu này.

## Cấu trúc project

```text
.
├── algorithms/
│   ├── __init__.py
│   ├── direct_scan.py
│   ├── two_pointers.py
│   ├── transform_and_conquer.py
│   ├── divide_and_conquer.py
├── core/
├── history/
├── ui/
├── app.py
├── main.py
├── requirements.txt
└── README.md
```

## Yêu cầu môi trường

- Python `3.9+`
- `Tkinter`
- `matplotlib`

Lưu ý:

- Trên Windows, `Tkinter` thường đi kèm Python chính thức.
- Trên Ubuntu / Debian, nếu thiếu Tkinter, cài thêm:

```bash
sudo apt install python3-tk
```

## Cài đặt bằng virtual environment

### Windows PowerShell

1. Tạo virtual environment:

```powershell
python -m venv venv
```

2. Kích hoạt:

```powershell
.\venv\Scripts\Activate.ps1
```

3. Nếu PowerShell chặn script:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\venv\Scripts\Activate.ps1
```

4. Cập nhật `pip` và cài dependency:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. Chạy ứng dụng:

```powershell
python main.py
```

### Windows PowerShell không cần activate

Nếu không muốn activate `venv`, có thể chạy trực tiếp:

```powershell
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe main.py
```

### Linux / macOS

1. Tạo virtual environment:

```bash
python3 -m venv venv
```

2. Kích hoạt:

```bash
source venv/bin/activate
```

3. Cài dependency:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Chạy ứng dụng:

```bash
python main.py
```

## Chạy project

Entry point chính:

```bash
python main.py
```

Hoặc:

```bash
python app.py
```

## Cách sử dụng GUI

### Tab `Chạy test`

- Nhập `n`, `seed`, `tỷ lệ âm`, `số lần chạy`
- Chọn 1 thuật toán
- Bấm `Xem trước dữ liệu` để xem phân bố dấu trước khi chạy
- Bấm `Chạy 1 thuật toán` để benchmark thuật toán đang chọn
- Bấm `Benchmark 4 thuật toán` để chạy toàn bộ trên cùng một base array
- Chọn một dòng trong bảng tổng kết để xem:
  - `Before / After`
  - biên `k`
  - runtime
  - trạng thái `partition_ok / k_ok / ok`
  - thông tin batch / dataset

### Tab `Plot lịch sử`

- xem runtime trung bình theo kích thước `n`
- lọc theo dataset / batch
- multi-select thuật toán
- hover để xem giá trị
- click legend để ẩn / hiện từng line
- xuất PNG

## Output sau khi chạy

Mặc định project lưu kết quả vào thư mục `outputs/`:

```text
outputs/
├── results.csv
└── arrays/
    └── array_*.json
```

Trong đó:

- `results.csv`: log benchmark tổng hợp
- `arrays/array_*.json`: chỉ lưu khi cấu hình cho phép, thường dùng để debug case lỗi

Thư mục `outputs/` đã được đưa vào `.gitignore`, nên không nên commit lên GitHub.

## Public API

`algorithms/__init__.py` export các hàm sau:

- `partition_direct_scan`
- `partition_two_pointers`
- `partition_transform_and_conquer`
- `partition_divide_and_conquer`
- `OFFICIAL_ALGORITHM_SPECS`
- `OFFICIAL_ALGORITHM_LABELS`
- `ALGORITHM_DETAILS`

Ngoài ra, input public API hiện fail-fast nếu mảng chứa `0`, thông qua:

```python
from core.validation import validate_partition_input
```

## Tính đúng của bài toán

Sau khi chạy một thuật toán hợp lệ:

- `A[:k]` chỉ chứa số âm
- `A[k:]` chỉ chứa số dương
- hàm trả về `k = số phần tử âm`

Ví dụ:

```text
A = [3, -2, 5, -7, 8]
Sau phân hoạch: [-2, -7, 3, 5, 8], k = 2
```

## Troubleshooting

### 1. Lỗi `No module named matplotlib`

```bash
pip install -r requirements.txt
```

### 2. Lỗi Tkinter / `init.tcl`

- Hãy dùng Python được cài kèm Tcl/Tk đầy đủ.
- Trên Windows, nên dùng Python chính thức từ python.org.
- Nếu đang dùng nhiều interpreter, hãy chắc là bạn cài dependency và chạy app trên cùng một interpreter.

### 3. PowerShell không cho chạy `Activate.ps1`

Chạy:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

### 4. Không muốn activate `venv`

Chạy trực tiếp bằng interpreter trong `venv`:

```powershell
.\venv\Scripts\python.exe main.py
```

## Chuẩn bị upload GitHub

Repo này đã được chuẩn hóa để upload dễ hơn:

- `README.md` có hướng dẫn cài đặt và chạy
- `requirements.txt` có dependency cần thiết
- `.gitignore` bỏ qua `venv`, cache, IDE files, và benchmark output

Trước khi push, nên kiểm tra:

```bash
python -m py_compile app.py main.py
```

## License

Hiện repo chưa khai báo license. Nếu bạn định public trên GitHub, nên thêm một file `LICENSE` phù hợp như `MIT`.
