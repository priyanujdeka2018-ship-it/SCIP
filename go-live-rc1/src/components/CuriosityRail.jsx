/* SCIP CuriosityRail — chip row beneath answers (prototype verbatim). */
export default function CuriosityRail({ items, onChoose }) {
  return (
    <div className="curiosity">
      {items.map((it) => (
        <button key={it.k} className="chip" onClick={() => onChoose(it.k)}>{it.label}</button>
      ))}
    </div>
  );
}
