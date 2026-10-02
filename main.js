(() => {
  // コレクションの絞り込み
  const chips = document.querySelectorAll(".chip");
  const items = document.querySelectorAll(".specimen");
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const type = chip.dataset.filter;
      chips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
      items.forEach((it) => { it.hidden = type !== "all" && it.dataset.type !== type; });
    });
  });

  // 生育カレンダーに今月の印をつける
  const month = new Date().getMonth() + 1;
  document.querySelectorAll(`.cal [data-m="${month}"]`).forEach((el) => el.classList.add("now"));

  // Instagram ID のコピー
  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const text = btn.dataset.copy;
      // 連続で押しても元の文言に戻るよう、最初の表示を覚えておく
      btn.dataset.label ??= btn.textContent;
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = "コピーしました";
      } catch {
        // コピーできない環境では、IDを表示して手で写せるようにする
        btn.textContent = text;
      }
      clearTimeout(btn._reset);
      btn._reset = setTimeout(() => { btn.textContent = btn.dataset.label; }, 2400);
    });
  });
})();
