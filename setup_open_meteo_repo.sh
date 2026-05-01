#!/usr/bin/env bash
# =============================================================================
# setup_open_meteo_repo.sh
# Tworzy nowe repo Git dla integracji open-meteo-weather
# Uruchom z katalogu homepulse:  bash setup_open_meteo_repo.sh
# =============================================================================
set -e

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$(dirname "$SRC")/open-meteo-weather"

echo "=================================================="
echo "  Open-Meteo Weather — tworzenie nowego repo"
echo "  Cel: $DEST"
echo "=================================================="

# 1. Utwórz katalog docelowy
if [ -d "$DEST" ]; then
  echo "⚠️  Katalog $DEST już istnieje. Nadpisać? (t/n)"
  read -r ans
  [[ "$ans" != "t" ]] && { echo "Anulowano."; exit 0; }
  rm -rf "$DEST"
fi
mkdir -p "$DEST"

# 2. Kopiuj custom_component
echo "📂 Kopiuję custom_components/open_meteo_weather..."
mkdir -p "$DEST/custom_components"
cp -r "$SRC/custom_components/open_meteo_weather" "$DEST/custom_components/"

# 3. Kopiuj pliki HACS (hacs.json, README.md, icon.svg)
echo "📄 Kopiuję pliki HACS..."
cp "$SRC/open_meteo_weather_hacs/hacs.json" "$DEST/hacs.json"
cp "$SRC/open_meteo_weather_hacs/README.md"  "$DEST/README.md"
cp "$SRC/open_meteo_weather_hacs/icon.svg"   "$DEST/icon.svg"

# 4. Utwórz .gitignore
cat > "$DEST/.gitignore" << 'EOF'
__pycache__/
*.pyc
*.pyo
.DS_Store
*.egg-info
.env
EOF

# 5. Zainicjuj git
echo "🔧 Inicjuję repozytorium Git..."
cd "$DEST"
git init
git add .
git commit -m "feat: Initial release v1.0.0 — Open-Meteo Weather integration"
git tag v1.0.0

echo ""
echo "✅ Gotowe! Repo utworzone w: $DEST"
echo ""
echo "Następne kroki:"
echo "  1. Utwórz nowe repo na GitHub: https://github.com/new"
echo "     Nazwa: open-meteo-weather  |  Publiczne  |  BEZ README"
echo ""
echo "  2. Dodaj remote i wypchnij:"
echo "     cd $DEST"
echo "     git remote add origin https://github.com/kamiljaworski88/open-meteo-weather.git"
echo "     git push -u origin main"
echo "     git push origin v1.0.0"
echo ""
echo "  3. Dodaj do HACS (własne repo):"
echo "     HACS → Integracje → ⋮ → Własne repozytoria"
echo "     URL: https://github.com/kamiljaworski88/open-meteo-weather"
echo "     Kategoria: Integration"
echo ""
echo "  4. (Opcjonalnie) Zgłoś do HACS default:"
echo "     https://github.com/hacs/default — PR do pliku integration"
echo "=================================================="
