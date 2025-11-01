async function getRates() {
  const res = await fetch("https://твой-домен.uz/api/p2p");
  const data = await res.json();
  if(data.error){
    document.getElementById("result").innerHTML = "⚠️ Нет данных.";
    return;
  }
  document.getElementById("result").innerHTML = `
    <p>🔼 BUY: ${data.buy}</p>
    <p>🔽 SELL: ${data.sell}</p>
    <p>📊 Spread: ${data.spread}</p>
  `;
}
