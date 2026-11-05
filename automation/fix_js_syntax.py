from pathlib import Path

path = Path(r"C:\Users\Andrés\.gemini\antigravity\scratch\manya_servicioti\js\app.js")
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "clkTxt.textContent" in line and "FINALIZADO" in line:
        print(f"Found line {i+1}: {line.strip()}")
        lines[i] = "      const estNom = (act && act.estadio && act.estadio.nombre) || (prox && prox.estadio && prox.estadio.nombre) || 'Estadio Centenario';\n      if (clkTxt) clkTxt.textContent = `🏁 FINALIZADO (90+5') • ${estNom.toUpperCase()}`;\n"

with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)
print("SUCCESS_FIXED_LINE")
