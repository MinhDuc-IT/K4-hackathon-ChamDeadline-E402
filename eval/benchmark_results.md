# Bảng kết quả chạy Benchmark

## Lượt chạy gần nhất: Evidence-faithful v2
**Thời gian:** 31/07/2026 04:07:44Z
**Mô hình Bot:** gpt-4o-mini
**Mô hình Judge:** gpt-5.6 (High reasoning)

## Kết quả chi tiết
| Metric | Điểm số | Quality Bar | Trạng thái |
|--------|---------|-------------|------------|
| Final Pass Rate | 15% (3/20) | ≥ 85% | ❌ Fail |
| Behavior Accuracy | 60% | ≥ 90% | ❌ Fail |
| Answer Correctness | N/A | ≥ 85% | ❌ Fail |
| Groundedness | 61.54% | ≥ 90% | ❌ Fail |
| Citation Accuracy | 53.85% | ≥ 90% | ❌ Fail |
| Abstention Accuracy| 60% | ≥ 80% | ❌ Fail |
| Conflict Resolution| 0% | 100% | ❌ Fail |
| Security Pass Rate | 100% | 100% | ✅ Pass |
| Hallucination Rate | 45% | 0% | ❌ Fail |

## Nhận xét & Vấn đề lớn nhất:
- **Lỗi đau nhất: Conflict giả.** Bot nhận diện sai các nguồn trung lập (neutral) thành đồng tình/phản đối và báo cáo là thông tin mâu thuẫn.
- **Citation thừa:** Đưa quá nhiều link dẫn tới việc giảm Citation Accuracy.

## Hành động tiếp theo:
- Fix relevance gate để lọc bớt nguồn `neutral`.
- Tách luồng mâu thuẫn ra và chỉ kích hoạt khi có 2 luồng trái ngược rõ rệt.
