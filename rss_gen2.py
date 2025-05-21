name: Actualizar RSS diario

on:
  schedule:
    - cron: '10 12 * * *'  # 6:10 AM hora de México (UTC-6 = 12:10 UTC)
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Clonar repositorio
        uses: actions/checkout@v3
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Configurar Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Instalar dependencias
        run: pip install requests

      - name: Ejecutar script RSS
        run: python rss_gen2.py

      - name: Hacer commit si hay cambios
        run: |
          git config --global user.name "github-actions"
          git config --global user.email "actions@github.com"
          git add dof_rss.xml
          git diff --cached --quiet || git commit -m "Actualizar RSS automático"
          git remote set-url origin https://x-access-token:${GITHUB_TOKEN}@github.com/${{ github.repository }}.git
          git push
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
