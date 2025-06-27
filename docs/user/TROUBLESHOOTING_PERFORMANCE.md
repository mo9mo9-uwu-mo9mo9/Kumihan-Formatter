# ⚡ パフォーマンス・最適化のトラブルシューティング

> **速度・メモリ・効率化に関する問題を解決**

[← トラブルシューティング目次に戻る](TROUBLESHOOTING.md)

---

## 📋 パフォーマンス問題一覧

- [変換が非常に遅い / ハングアップする](#-症状-変換が非常に遅い--ハングアップする)
- [文字数制限 / 極端に長い行のエラー](#-症状-文字数制限--極端に長い行のエラー)
- [メモリ不足 / システムが重くなる](#-症状-メモリ不足--システムが重くなる)

---

## ❌ **症状**: 変換が非常に遅い / ハングアップする

### 🔍 **原因**
- ファイルサイズが大きすぎる（10MB以上）
- 大量の画像ファイル
- 複雑な記法の多用
- メモリ不足

### ✅ **解決方法**

#### **Step 1: ファイルサイズの確認**
```bash
# ファイルサイズ確認
ls -lh *.txt                # macOS/Linux
dir *.txt                   # Windows

# 行数確認
wc -l document.txt          # macOS/Linux
find /c /v "" document.txt  # Windows

# 文字数確認
wc -c document.txt          # macOS/Linux
```

**推奨制限値:**
- **ファイルサイズ**: 1MB以下
- **行数**: 10,000行以下
- **文字数**: 500,000文字以下

#### **Step 2: ファイル分割での対処**

**大きなファイルの分割例:**
```bash
# 行数で分割（1000行ごと）
split -l 1000 large_file.txt chapter_

# サイズで分割（500KB毎）
split -b 500k large_file.txt part_

# 手動分割の例
head -n 1000 large_file.txt > chapter1.txt
tail -n +1001 large_file.txt | head -n 1000 > chapter2.txt
```

**分割後の一括変換:**
```bash
# 複数ファイルを一度に変換
python -m kumihan_formatter chapter*.txt

# 設定ファイル適用での一括変換
python -m kumihan_formatter chapter*.txt --config config.yaml
```

#### **Step 3: メモリ使用量の監視**

**Windows:**
```powershell
# リアルタイムメモリ監視
Get-Process python | Select-Object ProcessName, @{Name="Memory(MB)";Expression={[math]::Round($_.WorkingSet/1MB,2)}}

# 継続監視
while ($true) { Get-Process python -ErrorAction SilentlyContinue | Select-Object @{Name="Memory(MB)";Expression={[math]::Round($_.WorkingSet/1MB,2)}}; Start-Sleep 2 }
```

**macOS:**
```bash
# メモリ使用量確認
top -pid $(pgrep python) -l 1

# 継続監視
watch "ps aux | grep python | grep -v grep"
```

#### **Step 4: 軽量モードでの実行（将来実装）**
```bash
# 軽量モード（画像処理なし）
python -m kumihan_formatter large_file.txt --lightweight

# ストリーミングモード（部分的処理）
python -m kumihan_formatter large_file.txt --streaming

# プログレスバー表示
python -m kumihan_formatter large_file.txt --progress
```

---

## ❌ **症状**: 文字数制限 / 極端に長い行のエラー

### 🔍 **原因**
- 改行なしの極端に長い行（10,000文字以上）
- バイナリファイルの誤読み込み
- エディタによる改行コード変換問題

### ✅ **解決方法**

#### **Step 1: 改行コードの正規化**
```bash
# 改行コード確認
file -b document.txt        # macOS/Linux
nkf -g document.txt         # 日本語環境の場合

# CRLF → LF変換
dos2unix document.txt       # macOS/Linux

# Windows（PowerShell）
(Get-Content document.txt) -join "`n" | Set-Content document_fixed.txt
```

#### **Step 2: 長い行の確認と分割**
```bash
# 行の長さ確認
awk '{print length($0), NR}' document.txt | sort -nr | head -10

# 極端に長い行を特定
awk 'length($0) > 1000 {print "Line " NR ": " length($0) " characters"}' document.txt
```

**手動での行分割:**
```text
# 悪い例（1行が長すぎる）
これは非常に長い文章で、改行がなく、ブラウザでの表示やプログラムでの処理が困難になります。このような長い行は避けるべきです。

# 良い例（適度な長さで改行）
これは適度な長さで改行された文章です。
読みやすく、処理も効率的に行えます。
```

#### **Step 3: ファイル形式の確認**
```bash
# ファイル形式確認
file document.txt           # macOS/Linux

# テキストファイルか確認
head -c 100 document.txt | cat -v
```

**バイナリファイルの場合:**
- Word文書（.docx）をテキストで開いている
- PDF、画像ファイルの誤認識
- 圧縮ファイルの誤認識

**対処法:**
```bash
# Word文書からテキスト抽出（要pandoc）
pandoc document.docx -t plain -o document.txt

# PDFからテキスト抽出（要pdftotext）
pdftotext document.pdf document.txt
```

---

## ❌ **症状**: メモリ不足 / システムが重くなる

### 🔍 **原因**
- 大量の画像ファイル処理
- メモリリークの発生
- システムの利用可能メモリ不足

### ✅ **解決方法**

#### **Step 1: 画像最適化**
```bash
# 画像ファイルサイズ確認
du -sh images/              # macOS/Linux
dir images\ /s              # Windows

# 大きな画像ファイル特定
find images/ -size +1M -ls  # macOS/Linux
```

**画像最適化の手法:**

```bash
# JPEG圧縮（要ImageMagick）
magick image.jpg -quality 85 image_optimized.jpg

# PNG最適化（要OptiPNG）
optipng -o7 image.png

# 一括リサイズ（幅1200px以下）
magick mogrify -resize 1200x image*.jpg
```

**推奨画像仕様:**
- **最大幅**: 1200px
- **JPEG品質**: 85%
- **1ファイル**: 500KB以下
- **総容量**: 10MB以下

#### **Step 2: システムリソース確認**
```bash
# 利用可能メモリ確認
free -h                     # Linux
vm_stat                     # macOS

# Windows（PowerShell）
Get-WmiObject -Class Win32_ComputerSystem | Select-Object TotalPhysicalMemory
Get-Counter "\Memory\Available MBytes"
```

#### **Step 3: 段階的処理**
```bash
# 画像なしで変換テスト
mkdir images_backup
mv images/* images_backup/
python -m kumihan_formatter document.txt

# 画像を段階的に戻す
mv images_backup/small_image.jpg images/
python -m kumihan_formatter document.txt
```

---

## 🚀 **パフォーマンス最適化のベストプラクティス**

### **ファイル管理**
```
最適な構成:
project/
├── main.txt              ← 5MB以下
├── images/               ← 合計10MB以下
│   ├── thumb_*.jpg       ← 各500KB以下
│   └── diagram_*.png     ← 各1MB以下
└── backup/               ← 大容量ファイルは別保存
    └── original_large.txt
```

### **記法最適化**
```text
# 重い記法の使い分け
;;;見出し1                  # 軽量
タイトル
;;;

;;;太字                     # 軽量  
重要情報
;;;

;;;太字+枠線+ハイライト      # やや重い
複合スタイル
;;;

;;;ネタバレ                 # 軽量（JSなし）
隠しコンテンツ
;;;
```

### **バッチ処理の活用**
```bash
# 効率的なバッチ処理
for file in *.txt; do
    echo "Processing $file..."
    python -m kumihan_formatter "$file" --no-preview
done

# 並列処理（要GNU parallel）
parallel python -m kumihan_formatter {} --no-preview ::: *.txt
```

---

## 📊 **パフォーマンス監視ツール**

### **変換時間測定**
```bash
# 実行時間測定
time python -m kumihan_formatter document.txt

# 詳細な時間測定
/usr/bin/time -v python -m kumihan_formatter document.txt  # Linux
```

### **プロファイリング（開発者向け）**
```bash
# Pythonプロファイリング
python -m cProfile -s cumulative -m kumihan_formatter document.txt

# メモリプロファイリング（要memory_profiler）
python -m memory_profiler -m kumihan_formatter document.txt
```

---

## 🎯 **推奨システム要件**

### **最小要件**
- **CPU**: 1GHz以上
- **メモリ**: 2GB以上
- **ストレージ**: 100MB以上の空き容量

### **推奨要件**
- **CPU**: 2GHz以上
- **メモリ**: 4GB以上
- **ストレージ**: 1GB以上の空き容量
- **SSD**: 推奨（HDDより高速）

### **大容量処理要件**
- **CPU**: 4コア以上
- **メモリ**: 8GB以上
- **ストレージ**: 5GB以上の空き容量

---

## 📞 **サポートが必要な場合**

パフォーマンス問題の報告テンプレート：

```
## パフォーマンス問題報告

### システム情報
- CPU: [Intel i5-8400 / Apple M1 など]
- メモリ: [8GB / 16GB など]
- ストレージ: [SSD / HDD]
- OS: [Windows 10 / macOS Big Sur など]

### ファイル情報
- ファイルサイズ: [MB]
- 行数: [行]
- 画像ファイル数: [個]
- 画像総容量: [MB]

### パフォーマンス問題
- 実行時間: [実際の時間 / 期待時間]
- メモリ使用量: [最大使用量]
- CPU使用率: [使用率]
- エラーメッセージ: [もしあれば]

### 試した最適化
- [ ] ファイル分割
- [ ] 画像最適化
- [ ] 軽量モード実行
- [ ] メモリ監視
```

---

## 📚 関連リソース

- **[トラブルシューティング目次](TROUBLESHOOTING.md)** - 他の問題も確認
- **[実践ガイド](PRACTICAL_GUIDE.md)** - 効率的なワークフロー
- **[高度なトラブルシューティング](TROUBLESHOOTING_ADVANCED.md)** - デバッグ手法

---

**パフォーマンス問題が解決することを願っています！ ⚡✨**