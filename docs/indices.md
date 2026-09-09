# METRIC 光譜與應力指數參考

本檔涵蓋 METRIC ET 管線中所有光譜指數（per-scene）與時空應力指數。共 **17 個指數**，分為三大類別：光譜指數、地表應力指數、時空應力指數。

---

## 一、光譜指數（Spectral Indices）

所有光譜指數於 Stage 3b 計算，讀取 Landsat 8/9 原始反射率波段。缺 band 時跳過並記錄警告，不中斷管線。

### 1. NDMI — Normalized Difference Moisture Index（歸一化Difference水分指數）

| 項目 | 內容 |
|------|------|
| **公式** | `NDMI = (NIR − SWIR1) / (NIR + SWIR1)` |
| **Landsat 8/9 寫法** | `(B5 − B6) / (B5 + B6)` |
| **所需波段** | `nir08`（B5）、`swir16`（B6） |
| **有效範圍** | [−1, 1] |
| **物理意義** | 測量植物葉片與土壤水分含量；數值越高表示水分越充足，常用於乾旱監測 |
| **所屬目錄** | `spectral_indices` |
| **原始碼** | `metric_et/surface/moisture.py::NDMI` |

---

### 2. MSI — Moisture Stress Index（水分應力指數）

| 項目 | 內容 |
|------|------|
| **公式** | `MSI = SWIR1 / NIR` |
| **Landsat 8/9 寫法** | `B6 / B5` |
| **所需波段** | `nir08`（B5）、`swir16`（B6） |
| **有效範圍** | 無固定上限，通常 0.3–3.0 |
| **物理意義** | 衡量植物水分壓力；數值越高表示水分壓力越大（乾燥土壤或缺水植物） |
| **所屬目錄** | `spectral_indices` |
| **原始碼** | `metric_et/surface/moisture.py::MSI` |

---

### 3. NMDI — Normalized Multi-band Drought Index（多波段歸一化乾旱指數）

| 項目 | 內容 |
|------|------|
| **公式** | `NMDI = (NIR − (SWIR1 − SWIR2)) / (NIR + (SWIR1 − SWIR2))` |
| **Landsat 8/9 寫法** | `(B5 − (B6 − B7)) / (B5 + (B6 − B7))` |
| **所需波段** | `nir08`（B5）、`swir16`（B6）、`swir22`（B7） |
| **有效範圍** | [−1, 1] |
| **物理意義** | 比 NDMI 更敏感於大氣水汽干擾，適合區域性乾旱評估；數值越高表示水分條件越好 |
| **所屬目錄** | `spectral_indices` |
| **原始碼** | `metric_et/surface/moisture.py::NMDI` |

---

### 4. NIRv — Near-Infrared Reflectance of Vegetation（植被近紅外反射率）

| 項目 | 內容 |
|------|------|
| **公式** | `NIRv = NDVI × NIR` |
| **Landsat 8/9 寫法** | `NDVI × B5` |
| **所需波段** | `ndvi`（預先計算）、`nir08`（B5） |
| **有效範圍** | 約 [0, 0.5] |
| **物理意義** | 結合植被綠度與近紅外反射，是 GPP（ gross primary production）與生物量的強力預測指標 |
| **所屬目錄** | `spectral_indices` |
| **原始碼** | `metric_et/surface/productivity.py::NIRv` |

---

### 5. GCI — Green Chlorophyll Index（綠色葉綠素指數）

| 項目 | 內容 |
|------|------|
| **公式** | `GCI = (NIR / Green) − 1` |
| **Landsat 8/9 寫法** | `(B5 / B3) − 1` |
| **所需波段** | `nir08`（B5）、`green`（B3） |
| **有效範圍** | 通常 1–10，密集植被可 > 2 |
| **物理意義** | 反映葉片葉綠素與氮含量；數值越高表示葉綠素濃度越高，可用於作物營養診斷 |
| **所屬目錄** | `spectral_indices` |
| **原始碼** | `metric_et/surface/productivity.py::GCI` |

---

### 6. NDSI — Normalized Difference Salinity Index（歸一化 Difference 鹽分指數）

| 項目 | 內容 |
|------|------|
| **公式** | `NDSI = (Red − NIR) / (Red + NIR)` |
| **Landsat 8/9 寫法** | `(B4 − B5) / (B4 + B5)` |
| **所需波段** | `red`（B4）、`nir08`（B5） |
| **有效範圍** | [−1, 1] |
| **物理意義** | 正值表示鹽鹼地或都市表面；負值表示健康植被。用於土壤鹽分與土地退化監測 |
| **所屬目錄** | `spectral_indices` |
| **原始碼** | `metric_et/surface/salinity.py::NDSI` |

---

### 7. SI_T — Soil Salinity Index（幾何平均變體土壤鹽分指數）

| 項目 | 內容 |
|------|------|
| **公式** | `SI_T = √(Red × SWIR1)` |
| **Landsat 8/9 寫法** | `√(B4 × B6)` |
| **所需波段** | `red`（B4）、`swir16`（B6） |
| **有效範圍** | ≥ 0（反射率縮放單位） |
| **物理意義** | 結合红光與短波紅外的幾何平均，對農業土壤鹽分較 NDSI 更敏感 |
| **所屬目錄** | `spectral_indices` |
| **原始碼** | `metric_et/surface/salinity.py::SI_T` |

---

## 二、地表應力指數（Per-Scene Stress Indices）

此類指數於 Stage 3（surface properties）計算，需要 NDVI 與 LST 已存在於 DataCube 中。

### 8. CWSI_LST — Crop Water Stress Index（NDVI-LST 特徵空間法）

| 項目 | 內容 |
|------|------|
| **公式** | `CWSI_LST = (LST − LST_wet) / (LST_dry − LST_wet)` |
| **所需波段** | `ndvi`、`lst` |
| **有效範圍** | [0, 1]（預設 clip） |
| **物理意義** | 0 = 水分充足；1 = 最大水分壓力。以 NDVI 分箱，取每箱 LST 的 wet（5%分位）與 dry（95%分位）邊界插值得到 |
| **所屬目錄** | `stress_indices` |
| **原始碼** | `metric_et/surface/stress.py::CWSILSTCalculator` |

---

### 9. TVDI — Temperature Vegetation Dryness Index（溫植被乾旱指數）

| 項目 | 內容 |
|------|------|
| **公式** | `TVDI = (LST − LST_min) / (LST_max − LST_min)` |
| **所需波段** | `ndvi`、`lst` |
| **有效範圍** | [0, 1]（預設 clip） |
| **物理意義** | 0 = 濕邊（水分充足）；1 = 乾邊（嚴重缺水）。以 NDVI 分箱後以 polyfit 擬合乾邊線 |
| **所屬目錄** | `stress_indices` |
| **原始碼** | `metric_et/surface/stress.py::TVDICalculator` |

---

### 10. VSWI — Vegetation Supply Water Index（植被供水水指數）

| 項目 | 內容 |
|------|------|
| **公式** | `VSWI = NDVI / LST` |
| **所需波段** | `ndvi`、`lst` |
| **有效範圍** | 無固定上限 |
| **物理意義** | 瞬時水分供應指標；數值越高表示相對水分條件越好。**注意：LST 必須為開爾文（K）** |
| **所屬目錄** | `stress_indices` |
| **原始碼** | `metric_et/surface/stress.py::VSWI` |

---

### 11. CWSI_ET — Crop Water Stress Index（ET 比值法）

| 項目 | 內容 |
|------|------|
| **公式** | `CWSI_ET = 1 − (ET_inst / ETrF_inst)` |
| **所需數據** | `ET_inst`、`ETrF`（由 ET 管線計算） |
| **有效範圍** | [0, 1] |
| **物理意義** | 0 = 水分充足；1 = 最大水分壓力。此為 ET 模型內部指標，在 `calculate_et()` 中直接計算，不經獨立模組 |
| **所屬目錄** | `stress_indices` |
| **原始碼** | `metric_et/pipeline/metric_pipeline.py::calculate_et()` |

---

## 三、時空應力指數（Temporal Stress Indices）

此類指數需累積多景影像的 NDVI/LST 最小/最大值後計算，於 `_compute_temporal_indices()` 執行。

### 12. VCI — Vegetation Condition Index（植被狀況指數）

| 項目 | 內容 |
|------|------|
| **公式** | `VCI = (NDVI − NDVI_min) / (NDVI_max − NDVI_min)` |
| **所需數據** | 各景累積的 `ndvi`、`ndvi_min`、`ndvi_max` |
| **有效範圍** | [0, 1] |
| **物理意義** | 0 = 最差植被狀況；1 = 最佳植被狀況。分母為零時該像素返回 NaN |
| **所屬目錄** | `stress_indices`（時空部分） |
| **原始碼** | `metric_et/surface/temporal_stress.py::VCI` |

---

### 13. TCI — Temperature Condition Index（溫度狀況指數）

| 項目 | 內容 |
|------|------|
| **公式** | `TCI = (LST_max − LST) / (LST_max − LST_min)` |
| **所需數據** | 各景累積的 `lst`、`lst_min`、`lst_max`，以及最新一景的 `lst` 作為瞬間值 |
| **有效範圍** | [0, 1] |
| **物理意義** | 0 = 最熱/最大壓力；1 = 最涼/最健康。分母為零時該像素返回 NaN |
| **所屬目錄** | `stress_indices`（時空部分） |
| **原始碼** | `metric_et/surface/temporal_stress.py::TCI` |

---

### 14. VHI — Vegetation Health Index（植被健康指數）

| 項目 | 內容 |
|------|------|
| **公式** | `VHI = α·VCI + (1 − α)·TCI`（預設 α = 0.5） |
| **所需數據** | `vci`、`tc i`（同景） |
| **有效範圍** | [0, 1] |
| **物理意義** | 綜合植被綠度與溫度壓力；任一輸入為 NaN 則結果為 NaN |
| **所屬目錄** | `stress_indices`（時空部分） |
| **原始碼** | `metric_et/surface/temporal_stress.py::VHI` |

---

## 四、輸出目錄對照表

| 目錄 (output_categories) | 包含指數 |
|--------------------------|---------|
| `et_core` | ET_daily, ET_inst, ETrF, LE |
| `energy_balance` | R_n, G, H |
| `quality` | ET_quality_class, ETa_class |
| `surface_props` | NDVI, EVI, LAI, FVC, SAVI, Albedo, LST, Emissivity |
| `radiation` | R_ns, R_nl, Rs_down, R_l_down, R_l_up |
| `spectral_indices` | NDVI, SAVI, EVI, **NDMI, MSI, NMDI, NIRv, GCI, NDSI, SI_T** |
| `stress_indices` | **CWSI_ET, CWSI_LST, TVDI, VSWI, TCI, VCI, VHI** |

### Preset 對照

| Preset | 啟用目錄 |
|--------|---------|
| `minimal` | `et_core` |
| `standard` | `et_core`, `energy_balance`, `surface_props` |
| `full` | 全部七個目錄 |

---

## 五、使用方式

### Python API
```python
from metric_et.surface.moisture import NDMI, MSI, NMDI
from metric_et.surface.productivity import NIRv, GCI
from metric_et.surface.salinity import NDSI, SI_T
from metric_et.surface.stress import CWSILSTCalculator, TVDICalculator, VSWI
from metric_et.surface.temporal_stress import TCI, VCI, VHI

# Per-scene: compute() modifies cube in-place
cube = NDMI().compute(cube)   # adds 'ndmi' band
cube = MSI().compute(cube)    # adds 'msi' band
# ...

# Temporal (requires pre-computed min/max arrays):
tci_result = TCI().compute(lst_current, lst_min, lst_max)
vci_result = VCI().compute(ndvi_current, ndvi_min, ndvi_max)
vhi_result = VHI(alpha=0.5).compute(vci_result, tci_result)
```

### CLI
```bash
metric --output-categories et_core,spectral_indices,stress_indices \
       --roi roi.geojson --output ./out \
       --start-date 2024-01-01 --end-date 2024-03-31
```
