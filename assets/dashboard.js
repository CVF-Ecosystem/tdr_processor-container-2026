const {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback
} = React;
const C = {
  blue: "#3B82F6",
  green: "#10B981",
  amber: "#F59E0B",
  red: "#EF4444",
  slate: "#64748B",
  cyan: "#06B6D4",
  pink: "#EC4899",
  teal: "#14B8A6",
  orange: "#F97316"
};
let KPI_TARGET = 45;
const SP0 = {
  v: [0, 0, 0, 0, 0, 0, 0, 0],
  t: [0, 0, 0, 0, 0, 0, 0, 0],
  ps: [0, 0, 0, 0, 0, 0, 0, 0],
  nw: [0, 0, 0, 0, 0, 0, 0, 0],
  nm: [0, 0, 0, 0, 0, 0, 0, 0],
  dl: [0, 0, 0, 0, 0, 0, 0, 0],
  de: [0, 0, 0, 0, 0, 0, 0, 0],
  dh: [0, 0, 0, 0, 0, 0, 0, 0]
};
function Spark({
  data,
  color = "#3B82F6",
  w = 56,
  h = 22
}) {
  if (!data?.length) return null;
  const mn = Math.min(...data),
    mx = Math.max(...data),
    rng = mx - mn || 1;
  const pts = data.map((v, i) => `${i / (data.length - 1) * (w - 4) + 2},${h - (v - mn) / rng * (h - 4) - 2}`).join(" ");
  const lx = w - 2,
    lv = data[data.length - 1],
    ly = h - (lv - mn) / rng * (h - 4) - 2;
  return /*#__PURE__*/React.createElement("svg", {
    width: w,
    height: h,
    viewBox: `0 0 ${w} ${h}`,
    style: {
      overflow: "visible"
    }
  }, /*#__PURE__*/React.createElement("polyline", {
    points: pts,
    fill: "none",
    stroke: color,
    strokeWidth: "1.5",
    strokeLinejoin: "round",
    strokeLinecap: "round"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: lx,
    cy: ly,
    r: "2",
    fill: color
  }));
}
function KpiCard({
  lbl,
  val,
  unit,
  dl,
  dlt,
  icon,
  ic,
  spark
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "kc"
  }, /*#__PURE__*/React.createElement("div", {
    className: "kc-top"
  }, /*#__PURE__*/React.createElement("div", {
    className: "kc-lbl"
  }, lbl), /*#__PURE__*/React.createElement("div", {
    className: "kc-ico",
    style: {
      background: `${ic}18`
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: ic,
      fontSize: 11
    }
  }, icon))), /*#__PURE__*/React.createElement("div", {
    className: "kc-val"
  }, val, unit && /*#__PURE__*/React.createElement("span", null, unit)), /*#__PURE__*/React.createElement("div", {
    className: "kc-bot"
  }, /*#__PURE__*/React.createElement("div", {
    className: `kc-dl ${dlt}`
  }, dlt === "pos" ? "↑" : dlt === "neg" ? "↓" : "→", " ", dl), /*#__PURE__*/React.createElement(Spark, {
    data: spark,
    color: ic
  })));
}
function Sbadge({
  s
}) {
  const m = {
    Completed: "bg_",
    Berthed: "bb_",
    Anchored: "ba_",
    Departed: "bs_"
  };
  return /*#__PURE__*/React.createElement("span", {
    className: `bx ${m[s] || "bs_"}`
  }, s);
}
function Ebadge({
  t
}) {
  if (t === "Terminal Convenience") return /*#__PURE__*/React.createElement("span", {
    className: "bx br_"
  }, "Terminal");
  if (t === "Non-Terminal Convenience") return /*#__PURE__*/React.createElement("span", {
    className: "bx ba_"
  }, "Non-Terminal");
  return /*#__PURE__*/React.createElement("span", {
    className: "bx bp_"
  }, "Force Majeure");
}
function CCbadge({
  cat
}) {
  if (!cat) return null;
  const lower = cat.toLowerCase();
  const n = parseInt((cat.match(/\d+/) || [])[0] || "0");
  const cl = n === 1 ? "br_" : n === 2 ? "ba_" : n === 3 ? "bp_" : lower.includes("cran") || lower.includes("equip") ? "br_" : lower.includes("vessel") ? "ba_" : "bs_";
  return /*#__PURE__*/React.createElement("span", {
    className: `bx ${cl}`,
    style: {
      fontFamily: "var(--mono)",
      fontSize: 8.5
    }
  }, cat.length > 10 ? cat.substring(0, 10) + "…" : cat);
}
function ErrCodeBadge({
  code
}) {
  const m = {
    d: {
      cl: "br_",
      lbl: "TC"
    },
    i: {
      cl: "ba_",
      lbl: "NTC"
    },
    m: {
      cl: "bp_",
      lbl: "FM"
    },
    n: {
      cl: "ba_",
      lbl: "NTC"
    },
    a: {
      cl: "br_",
      lbl: "TC"
    }
  };
  const v = m[code] || {
    cl: "bs_",
    lbl: code || "—"
  };
  return /*#__PURE__*/React.createElement("span", {
    className: `bx ${v.cl}`,
    style: {
      fontFamily: "var(--mono)",
      fontSize: 8
    }
  }, v.lbl);
}
function renderPageButtons(activePg, totalPgs, onSelect) {
  const range = [];
  const maxBtns = 7;
  let start = Math.max(0, activePg - 3);
  let end = Math.min(totalPgs - 1, start + maxBtns - 1);
  if (end - start < maxBtns - 1) {
    start = Math.max(0, end - maxBtns + 1);
  }
  for (let i = start; i <= end; i++) {
    range.push(/*#__PURE__*/React.createElement("button", {
      key: i,
      className: `pb${i === activePg ? " ac" : ""}`,
      onClick: () => onSelect(i)
    }, i + 1));
  }
  return range;
}
function VesselTable({
  data,
  perPage = 20
}) {
  const [col, setCol] = useState("ata");
  const [dir, setDir] = useState("desc");
  const [pg, setPg] = useState(0);
  const sorted = useMemo(() => [...data].sort((a, b) => {
    let va = a[col],
      vb = b[col];
    if (va == null) va = dir === "asc" ? Infinity : -Infinity;
    if (vb == null) vb = dir === "asc" ? Infinity : -Infinity;
    if (typeof va === "string") return dir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
    return dir === "asc" ? va - vb : vb - va;
  }), [data, col, dir]);
  const rows = sorted.slice(pg * perPage, (pg + 1) * perPage);
  const pages = Math.ceil(data.length / perPage);
  const Th = ({
    c,
    l,
    r
  }) => /*#__PURE__*/React.createElement("th", {
    className: col === c ? dir === "asc" ? "sa" : "sd" : "",
    onClick: () => {
      if (col === c) setDir(d => d === "asc" ? "desc" : "asc");else {
        setCol(c);
        setDir("asc");
      }
      setPg(0);
    },
    style: r ? {
      textAlign: "right"
    } : {}
  }, l);
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "tw"
  }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: {
      width: 12
    }
  }), /*#__PURE__*/React.createElement(Th, {
    c: "name",
    l: "Vessel"
  }), /*#__PURE__*/React.createElement(Th, {
    c: "voyage",
    l: "Voyage"
  }), /*#__PURE__*/React.createElement(Th, {
    c: "op",
    l: "Operator"
  }), /*#__PURE__*/React.createElement(Th, {
    c: "berth",
    l: "Berth"
  }), /*#__PURE__*/React.createElement(Th, {
    c: "ata",
    l: "ATB",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "atd",
    l: "ATD",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "portstay",
    l: "Portstay h",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "net",
    l: "Net Wk h",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "cranes",
    l: "Cranes",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "ci",
    l: "VMPH",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "gmph",
    l: "GMPH",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "nmph",
    l: "NMPH",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "dis",
    l: "Disch.",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "load",
    l: "Load",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "conts",
    l: "Conts",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "teus",
    l: "TEUs",
    r: true
  }))), /*#__PURE__*/React.createElement("tbody", null, rows.map(v => /*#__PURE__*/React.createElement("tr", {
    key: v.id
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "5px 6px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 6,
      height: 6,
      borderRadius: "50%",
      background: v.nmph >= KPI_TARGET ? C.green : C.red
    }
  })), /*#__PURE__*/React.createElement("td", {
    className: "tb"
  }, v.name), /*#__PURE__*/React.createElement("td", {
    className: "tm",
    style: {
      color: "var(--t3)"
    }
  }, v.voyage), /*#__PURE__*/React.createElement("td", null, v.op), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("span", {
    className: "tm",
    style: {
      color: C.blue
    }
  }, v.berth)), /*#__PURE__*/React.createElement("td", {
    className: "tr tm"
  }, v.ata || "—"), /*#__PURE__*/React.createElement("td", {
    className: "tr tm",
    style: {
      color: "var(--t3)"
    }
  }, v.atd || "—"), /*#__PURE__*/React.createElement("td", {
    className: "tr"
  }, v.portstay != null ? v.portstay.toFixed(1) : "—"), /*#__PURE__*/React.createElement("td", {
    className: "tr"
  }, v.net.toFixed(1)), /*#__PURE__*/React.createElement("td", {
    className: "tr"
  }, v.cranes), /*#__PURE__*/React.createElement("td", {
    className: "tr",
    style: {
      color: "var(--t3)"
    }
  }, v.ci.toFixed(1)), /*#__PURE__*/React.createElement("td", {
    className: "tr"
  }, v.gmph.toFixed(1)), /*#__PURE__*/React.createElement("td", {
    className: "tr"
  }, /*#__PURE__*/React.createElement("div", {
    className: "kd"
  }, /*#__PURE__*/React.createElement("div", {
    className: "kd-dot",
    style: {
      background: v.nmph >= KPI_TARGET ? C.green : C.red
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      color: v.nmph >= KPI_TARGET ? C.green : C.red,
      fontWeight: 700
    }
  }, v.nmph.toFixed(1)))), /*#__PURE__*/React.createElement("td", {
    className: "tr"
  }, v.dis.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    className: "tr"
  }, v.load.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    className: "tr tb"
  }, v.conts.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    className: "tr",
    style: {
      color: "var(--t2)"
    }
  }, v.teus.toLocaleString())))))), /*#__PURE__*/React.createElement("div", {
    className: "pgr"
  }, /*#__PURE__*/React.createElement("span", {
    className: "pgi"
  }, pg * perPage + 1, "–", Math.min((pg + 1) * perPage, data.length), " of ", data.length, " · ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: C.green
    }
  }, data.filter(v => v.nmph >= KPI_TARGET).length, " above KPI"), " · ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: C.red
    }
  }, data.filter(v => v.nmph < KPI_TARGET).length, " below")), /*#__PURE__*/React.createElement("button", {
    className: "pb",
    onClick: () => setPg(p => p - 1),
    disabled: pg === 0
  }, "‹"), renderPageButtons(pg, pages, setPg), /*#__PURE__*/React.createElement("button", {
    className: "pb",
    onClick: () => setPg(p => p + 1),
    disabled: pg >= pages - 1
  }, "›")));
}
function DelayTable({
  data,
  perPage = 12
}) {
  const [col, setCol] = useState("dur");
  const [dir, setDir] = useState("desc");
  const [pg, setPg] = useState(0);
  const sorted = useMemo(() => [...data].sort((a, b) => {
    let va = a[col],
      vb = b[col];
    if (va == null) va = dir === "asc" ? Infinity : -Infinity;
    if (vb == null) vb = dir === "asc" ? Infinity : -Infinity;
    if (typeof va === "string") return dir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
    return dir === "asc" ? va - vb : vb - va;
  }), [data, col, dir]);
  const rows = sorted.slice(pg * perPage, (pg + 1) * perPage);
  const pages = Math.ceil(data.length / perPage);
  const Th = ({
    c,
    l,
    r
  }) => /*#__PURE__*/React.createElement("th", {
    className: col === c ? dir === "asc" ? "sa" : "sd" : "",
    onClick: () => {
      if (col === c) setDir(d => d === "asc" ? "desc" : "asc");else {
        setCol(c);
        setDir("desc");
      }
      setPg(0);
    },
    style: r ? {
      textAlign: "right"
    } : {}
  }, l);
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "tw"
  }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement(Th, {
    c: "vessel",
    l: "Vessel"
  }), /*#__PURE__*/React.createElement(Th, {
    c: "qc",
    l: "QC"
  }), /*#__PURE__*/React.createElement("th", null, "Stop"), /*#__PURE__*/React.createElement("th", null, "Code"), /*#__PURE__*/React.createElement(Th, {
    c: "from",
    l: "From"
  }), /*#__PURE__*/React.createElement(Th, {
    c: "to",
    l: "To"
  }), /*#__PURE__*/React.createElement(Th, {
    c: "dur",
    l: "Dur h",
    r: true
  }), /*#__PURE__*/React.createElement(Th, {
    c: "type",
    l: "Type"
  }))), /*#__PURE__*/React.createElement("tbody", null, rows.map(d => /*#__PURE__*/React.createElement("tr", {
    key: d.id
  }, /*#__PURE__*/React.createElement("td", {
    className: "tb",
    style: {
      maxWidth: 130,
      overflow: "hidden",
      textOverflow: "ellipsis"
    }
  }, d.vessel), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("span", {
    className: "bx bc_",
    style: {
      fontFamily: "var(--mono)"
    }
  }, d.qc)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement(CCbadge, {
    cat: d.cat
  })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement(ErrCodeBadge, {
    code: d.code
  })), /*#__PURE__*/React.createElement("td", {
    className: "tm"
  }, d.from), /*#__PURE__*/React.createElement("td", {
    className: "tm"
  }, d.to), /*#__PURE__*/React.createElement("td", {
    className: "tr"
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: d.dur >= 1 ? C.red : C.amber,
      fontWeight: 700
    }
  }, d.dur.toFixed(2), "h")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement(Ebadge, {
    t: d.type
  }))))))), /*#__PURE__*/React.createElement("div", {
    className: "pgr"
  }, /*#__PURE__*/React.createElement("span", {
    className: "pgi"
  }, pg * perPage + 1, "–", Math.min((pg + 1) * perPage, data.length), " of ", data.length, " · ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: C.red
    }
  }, data.filter(d => d.dur >= 1).length, " critical"), " · ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: C.amber
    }
  }, data.filter(d => d.dur < 1).length, " minor")), /*#__PURE__*/React.createElement("button", {
    className: "pb",
    onClick: () => setPg(p => p - 1),
    disabled: pg === 0
  }, "‹"), renderPageButtons(pg, pages, setPg), /*#__PURE__*/React.createElement("button", {
    className: "pb",
    onClick: () => setPg(p => p + 1),
    disabled: pg >= pages - 1
  }, "›")));
}
function QCGantt({
  timeline
}) {
  const W = 120;
  const toP = h => h / 24 * 100;
  const vc = {};
  timeline.forEach(r => r.segs.forEach(s => {
    vc[s.v] = s.col;
  }));
  return /*#__PURE__*/React.createElement("div", {
    className: "gnt-wrap"
  }, /*#__PURE__*/React.createElement("div", {
    className: "gnt-hdr"
  }, /*#__PURE__*/React.createElement("div", {
    className: "gnt-lbl",
    style: {
      width: W
    }
  }, "QC Crane"), /*#__PURE__*/React.createElement("div", {
    className: "gnt-axis",
    style: {
      paddingLeft: 8
    }
  }, [0, 4, 8, 12, 16, 20, 24].map(h => /*#__PURE__*/React.createElement("span", {
    key: h
  }, String(h).padStart(2, "0"), ":00")))), timeline.map(row => /*#__PURE__*/React.createElement("div", {
    key: row.qc,
    className: "gnt-row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "gnt-rl",
    style: {
      width: W
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "bx bc_",
    style: {
      fontFamily: "var(--mono)",
      fontSize: 9.5
    }
  }, row.qc)), /*#__PURE__*/React.createElement("div", {
    className: "gnt-trk",
    style: {
      marginLeft: 8
    }
  }, row.segs.map((seg, i) => {
    const l = toP(seg.from),
      w = Math.max(toP(seg.to) - l, .5);
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      className: "gnt-bar",
      style: {
        left: `${l}%`,
        width: `${w}%`,
        background: `${seg.col}CC`,
        borderLeft: `2px solid ${seg.col}`
      },
      title: `${row.qc}→${seg.v}`
    }, w > 6 ? seg.v.split(" ")[0] : "");
  })))), /*#__PURE__*/React.createElement("div", {
    className: "gnt-legs"
  }, Object.entries(vc).map(([v, col]) => /*#__PURE__*/React.createElement("div", {
    key: v,
    className: "gnt-leg"
  }, /*#__PURE__*/React.createElement("div", {
    className: "gnt-leg-dot",
    style: {
      background: col
    }
  }), v.split(" ").slice(0, 2).join(" ")))));
}
function DelayGantt({
  data
}) {
  const W = 120;
  const byV = useMemo(() => {
    const m = {};
    data.forEach(d => {
      if (!m[d.vessel]) m[d.vessel] = [];
      m[d.vessel].push(d);
    });
    return m;
  }, [data]);
  const ec = {
    d: C.red,
    i: C.amber,
    m: C.purple
  };
  const toP = t => {
    if (!t || t === "—") return 0;
    const timePart = t.includes(" ") ? t.split(" ")[1] : t;
    if (!timePart) return 0;
    const [h, m] = timePart.split(":").map(Number);
    return isNaN(h) ? 0 : (h + (m || 0) / 60) / 24 * 100;
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "gnt-wrap"
  }, /*#__PURE__*/React.createElement("div", {
    className: "gnt-hdr"
  }, /*#__PURE__*/React.createElement("div", {
    className: "gnt-lbl",
    style: {
      width: W
    }
  }, "Vessel"), /*#__PURE__*/React.createElement("div", {
    className: "gnt-axis",
    style: {
      paddingLeft: 8
    }
  }, [0, 4, 8, 12, 16, 20, 24].map(h => /*#__PURE__*/React.createElement("span", {
    key: h
  }, String(h).padStart(2, "0"), ":00")))), Object.entries(byV).map(([v, evs]) => /*#__PURE__*/React.createElement("div", {
    key: v,
    className: "gnt-row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "gnt-rl",
    style: {
      width: W
    },
    title: v
  }, v.split(" ").slice(0, 2).join(" ")), /*#__PURE__*/React.createElement("div", {
    className: "gnt-trk",
    style: {
      marginLeft: 8
    }
  }, evs.map((ev, i) => {
    const l = toP(ev.from),
      w = Math.max(toP(ev.to) - l, .5);
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      className: "gnt-bar",
      style: {
        left: `${l}%`,
        width: `${w}%`,
        background: `${ec[ev.code] || C.red}CC`,
        borderLeft: `2px solid ${ec[ev.code] || C.red}`
      },
      title: `${ev.rmk} ${ev.dur.toFixed(2)}h`
    }, w > 5 ? ev.rmk.substring(0, 12) : "");
  })))), /*#__PURE__*/React.createElement("div", {
    className: "gnt-legs"
  }, [["d", C.red, "Terminal Conv."], ["i", C.amber, "Non-Terminal Conv."], ["m", C.purple, "Force Majeure"]].map(([c, col, lbl]) => /*#__PURE__*/React.createElement("div", {
    key: c,
    className: "gnt-leg"
  }, /*#__PURE__*/React.createElement("div", {
    className: "gnt-leg-dot",
    style: {
      background: col
    }
  }), lbl))));
}
function BerthMap({
  berths
}) {
  const sc = {
    Berthed: C.blue,
    Available: "#1E293B",
    Anchored: C.amber
  };
  const sb = {
    Berthed: C.blue,
    Available: "#243048",
    Anchored: C.amber
  };

  // Better wave/water visualization
  const Waves = ({
    color
  }) => /*#__PURE__*/React.createElement("svg", {
    width: "100%",
    height: "24",
    viewBox: "0 0 120 24",
    preserveAspectRatio: "none",
    style: {
      opacity: 0.4
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "M0,12 C20,8 40,16 60,12 C80,8 100,16 120,12 V24 H0 Z",
    fill: color
  }), /*#__PURE__*/React.createElement("path", {
    d: "M0,16 C30,12 60,20 90,16 C120,12 150,20 180,16",
    fill: "none",
    stroke: color,
    strokeWidth: "1",
    strokeDasharray: "4 2"
  }));

  // Custom QC Crane Icon (Simple SVG)
  const QCIcon = ({
    color
  }) => /*#__PURE__*/React.createElement("svg", {
    width: "14",
    height: "14",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: color,
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M2 22h20"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M8 22V7l10-2v17"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M12 15h10"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M18 15V8"
  }));
  return /*#__PURE__*/React.createElement("div", {
    className: "bmap",
    style: {
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      minHeight: 180
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 2,
      background: "linear-gradient(90deg,transparent,#3B82F6,transparent)",
      borderRadius: 1
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      marginTop: 4,
      fontSize: 8,
      color: "var(--t4)",
      textTransform: "uppercase",
      letterSpacing: ".7px"
    }
  }, /*#__PURE__*/React.createElement("span", null, "◀ Sea Side / Quay Wall"), /*#__PURE__*/React.createElement("span", null, "Land Side ▶"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
      gap: 14,
      flex: 1
    }
  }, berths.map(b => /*#__PURE__*/React.createElement("div", {
    key: b.id,
    style: {
      background: b.status === "Available" ? "rgba(26,36,56,.3)" : "rgba(59,130,246,.08)",
      border: `1px solid ${sb[b.status] || "#243048"}`,
      borderTop: `4px solid ${sc[b.status] || "#1E293B"}`,
      borderRadius: 14,
      padding: "18px 20px",
      transition: "all .2s cubic-bezier(0.4, 0, 0.2, 1)",
      cursor: "default",
      display: "flex",
      flexDirection: "column",
      justifyContent: "space-between",
      position: 'relative',
      overflow: 'hidden',
      boxShadow: b.status !== "Available" ? '0 4px 20px rgba(0,0,0,0.15)' : 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      borderRadius: '50%',
      background: sc[b.status],
      opacity: 0.04,
      width: 90,
      height: 90,
      position: 'absolute',
      top: -25,
      right: -25,
      filter: 'blur(10px)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      fontWeight: 800,
      letterSpacing: "1px",
      color: "var(--t4)",
      textTransform: "uppercase",
      marginBottom: 8,
      opacity: 0.8
    }
  }, b.id), b.vessel ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 16,
      fontWeight: 800,
      color: "var(--t1)",
      lineHeight: 1.2,
      marginBottom: 4,
      letterSpacing: '-0.3px'
    }
  }, b.vessel), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--t3)",
      fontWeight: 600,
      marginBottom: 10,
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 12,
      height: 1.5,
      background: sc[b.status]
    }
  }), " ", b.op), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 2
    }
  }, Array.from({
    length: b.cranes || 1
  }).map((_, i) => /*#__PURE__*/React.createElement(QCIcon, {
    key: i,
    color: C.cyan
  }))), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9.5,
      color: C.cyan,
      fontWeight: 700,
      marginLeft: 2
    }
  }, b.cranes || 1, " QC"))) : /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 24,
      textAlign: 'center',
      fontSize: 11,
      fontWeight: 800,
      letterSpacing: 2,
      color: "var(--t4)",
      opacity: 0.5
    }
  }, "VACANT")), b.vessel && /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      margin: '12px 0 18px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 40,
      marginBottom: 0,
      filter: 'drop-shadow(0 6px 12px rgba(0,0,0,0.4))',
      position: 'relative',
      zIndex: 2
    }
  }, "🚢"), /*#__PURE__*/React.createElement("div", {
    style: {
      width: '100%',
      marginTop: -10
    }
  }, /*#__PURE__*/React.createElement(Waves, {
    color: sc[b.status]
  }))), b.vessel && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 7,
      background: "rgba(20,36,56,.7)",
      borderRadius: 3.5,
      marginBottom: 12,
      border: '1px solid var(--br)',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: "100%",
      width: `${b.pct}%`,
      background: `linear-gradient(90deg, ${sc[b.status]}, ${C.cyan})`,
      borderRadius: 3.5,
      transition: "width .5s ease-out"
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--t4)",
      display: 'flex',
      flexDirection: 'column',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--t1)'
    }
  }, b.pct, "%"), " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--t3)',
      fontSize: 9
    }
  }, "COMPLETE")), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--t1)'
    }
  }, b.conts), " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--t4)',
      fontSize: 9
    }
  }, "CONTS"))), b.atb && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 5,
      fontSize: 9.5,
      color: 'var(--t3)',
      background: 'var(--bg4)',
      padding: '4px 8px',
      borderRadius: 6,
      border: '1px solid var(--br2)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12
    }
  }, "⚓"), " ", b.atb)))))));
}
function SystemFeed({
  open,
  onToggle,
  initLines = []
}) {
  const [lines, setLines] = useState(initLines);
  const bodyRef = useRef(null);
  useEffect(() => {
    setLines(initLines);
  }, [initLines]);
  useEffect(() => {
    if (open && bodyRef.current) bodyRef.current.scrollTop = 0;
  }, [open]);
  const lc = {
    INFO: C.blue,
    WARN: C.amber,
    ERROR: C.red,
    SUCCESS: C.green
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "feed",
    style: {
      height: open ? 160 : 28
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "feed-hdr",
    onClick: onToggle
  }, /*#__PURE__*/React.createElement("div", {
    className: "feed-title"
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: C.green,
      fontSize: 8
    }
  }, "●"), "System & Processing Feed", /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9,
      color: "var(--t4)"
    }
  }, "— ", lines.length, " entries")), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: "var(--t4)"
    }
  }, open ? "▼" : "▲"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9,
      color: "var(--t4)",
      marginLeft: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: C.amber
    }
  }, lines.filter(l => l.lv === "WARN").length, " warn"), " · ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: C.red
    }
  }, lines.filter(l => l.lv === "ERROR").length, " err"))), open && /*#__PURE__*/React.createElement("div", {
    className: "feed-body",
    ref: bodyRef
  }, lines.map((l, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: `feed-line${l._new ? " fl-new" : ""}`
  }, /*#__PURE__*/React.createElement("span", {
    className: "fl-t"
  }, l.t), /*#__PURE__*/React.createElement("span", {
    className: "fl-lv",
    style: {
      color: lc[l.lv] || "var(--t3)"
    }
  }, "[", l.lv, "]"), /*#__PURE__*/React.createElement("span", {
    className: "fl-m"
  }, l.m)))));
}
function OpBarChart({
  data,
  kt = 45,
  theme = "dark"
}) {
  const ref = useRef(null);
  const ch = useRef(null);
  useEffect(() => {
    if (!ref.current) return;
    ch.current?.destroy();
    const ctx = ref.current.getContext("2d");
    const allVals = [...data.map(d => d.nmh), kt];
    const minV = Math.max(0, Math.floor(Math.min(...allVals) * 0.85));
    const maxV = Math.ceil(Math.max(...allVals) * 1.08);
    const isLight = theme === "light";
    const gridColor = isLight ? "rgba(226, 232, 240, 0.8)" : "rgba(20,36,56,.9)";
    const tickColor = isLight ? "#64748B" : "#3D556E";

    // Create gradients
    const greenGrad = ctx.createLinearGradient(0, 0, 0, 200);
    greenGrad.addColorStop(0, 'rgba(16,185,129,0.8)');
    greenGrad.addColorStop(1, 'rgba(16,185,129,0.2)');
    const redGrad = ctx.createLinearGradient(0, 0, 0, 200);
    redGrad.addColorStop(0, 'rgba(239,68,68,0.8)');
    redGrad.addColorStop(1, 'rgba(239,68,68,0.2)');
    const amberGrad = ctx.createLinearGradient(0, 0, 0, 200);
    amberGrad.addColorStop(0, 'rgba(245,158,11,0.8)');
    amberGrad.addColorStop(1, 'rgba(245,158,11,0.2)');
    const colors = data.map(d => {
      if (d.nmh >= kt) return greenGrad;
      if (d.nmh >= kt - 5) return amberGrad;
      return redGrad;
    });
    const borderColors = data.map(d => {
      if (d.nmh >= kt) return C.green;
      if (d.nmh >= kt - 5) return C.amber;
      return C.red;
    });
    ch.current = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.map(d => d.op),
        datasets: [{
          label: "Avg Net M/h",
          data: data.map(d => d.nmh),
          backgroundColor: colors,
          borderColor: borderColors,
          borderWidth: 1.5,
          borderRadius: 6,
          borderSkipped: false
        }, {
          label: `KPI (${kt})`,
          data: data.map(() => kt),
          type: "line",
          borderColor: C.blue,
          borderWidth: 2,
          borderDash: [6, 4],
          pointRadius: 0,
          fill: false,
          tension: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.raw.toFixed(1)} M/h`
            }
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: tickColor,
              font: {
                size: 10,
                weight: 600
              }
            }
          },
          y: {
            grid: {
              color: gridColor
            },
            border: {
              dash: [3, 3]
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9
              }
            },
            min: minV,
            max: maxV
          }
        }
      }
    });
    return () => ch.current?.destroy();
  }, [data, kt, theme]);
  return /*#__PURE__*/React.createElement("canvas", {
    ref: ref
  });
}
function MarketBarChart({
  data,
  theme = "dark"
}) {
  const ref = useRef(null);
  const ch = useRef(null);
  useEffect(() => {
    if (!ref.current || !data?.length) return;
    ch.current?.destroy();
    const ctx = ref.current.getContext("2d");
    const labels = data.map(d => d.op);
    const isL = theme === "light";
    const gridColor = isL ? "rgba(226,232,240,0.8)" : "rgba(20,36,56,.9)";
    const tickColor = isL ? "#64748B" : "#94A3B8";
    ch.current = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Discharge",
          data: data.map(d => d.dis),
          backgroundColor: C.blue + "CC",
          borderRadius: 4,
          barThickness: 18,
          maxBarThickness: 28
        }, {
          label: "Load",
          data: data.map(d => d.load),
          backgroundColor: C.green + "CC",
          borderRadius: 4,
          barThickness: 18,
          maxBarThickness: 28
        }]
      },
      options: {
        indexAxis: 'x',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color: tickColor,
              boxWidth: 10,
              font: {
                size: 10
              },
              usePointStyle: true,
              padding: 15
            }
          },
          tooltip: {
            borderWidth: 1,
            borderColor: "var(--br)"
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9,
                weight: 500
              }
            }
          },
          y: {
            grid: {
              color: gridColor
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9
              }
            }
          }
        }
      }
    });
    return () => ch.current?.destroy();
  }, [data, theme]);
  return /*#__PURE__*/React.createElement("canvas", {
    ref: ref
  });
}
function ContainerBarChart({
  data,
  theme = "dark",
  overrideColors = null
}) {
  const ref = useRef(null);
  const ch = useRef(null);
  useEffect(() => {
    if (!ref.current || !data?.length) return;
    ch.current?.destroy();
    const ctx = ref.current.getContext("2d");
    const labels = data.map(d => d.op);
    const isL = theme === "light";
    const tickColor = isL ? "#64748B" : "#94A3B8";
    const gridColor = isL ? "rgba(226, 232, 240, 0.8)" : "rgba(20,36,56,.9)";
    ch.current = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Full (Laden)",
          data: data.map(d => d.full),
          backgroundColor: (overrideColors?.full || C.blue) + "CC",
          borderRadius: 4,
          barThickness: 18,
          maxBarThickness: 28
        }, {
          label: "Empty",
          data: data.map(d => d.empty),
          backgroundColor: (overrideColors?.empty || "#3D556E") + "CC",
          borderRadius: 4,
          barThickness: 18,
          maxBarThickness: 28
        }]
      },
      options: {
        indexAxis: 'x',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color: tickColor,
              boxWidth: 10,
              font: {
                size: 10
              },
              usePointStyle: true,
              padding: 15
            }
          },
          tooltip: {
            borderWidth: 1,
            borderColor: "var(--br)"
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9,
                weight: 500
              }
            }
          },
          y: {
            grid: {
              color: gridColor
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9
              }
            }
          }
        }
      }
    });
    return () => ch.current?.destroy();
  }, [data, theme, overrideColors]);
  return /*#__PURE__*/React.createElement("canvas", {
    ref: ref
  });
}
function MarketTrendChart({
  data,
  theme = "dark"
}) {
  const ref = useRef(null);
  const ch = useRef(null);
  useEffect(() => {
    if (!ref.current || !data?.length) return;
    ch.current?.destroy();
    const isLight = theme === "light";
    const tickColor = isLight ? "#64748B" : "#3D556E";
    const gridColor = isLight ? "rgba(226, 232, 240, 0.8)" : "rgba(20,36,56,.9)";
    ch.current = new Chart(ref.current.getContext("2d"), {
      type: "line",
      data: {
        labels: data.map(d => d.date),
        datasets: [{
          label: "Total Volume (Conts)",
          data: data.map(d => d.volume),
          borderColor: C.blue,
          backgroundColor: "rgba(59,130,246,.08)",
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: C.blue,
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9
              }
            }
          },
          y: {
            grid: {
              color: gridColor
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9
              }
            }
          }
        }
      }
    });
    return () => ch.current?.destroy();
  }, [data, theme]);
  return /*#__PURE__*/React.createElement("canvas", {
    ref: ref
  });
}
function SizeMixBarChart({
  data,
  theme = "dark"
}) {
  const ref = useRef(null);
  const ch = useRef(null);
  useEffect(() => {
    if (!ref.current || !data?.length) return;
    ch.current?.destroy();
    const ctx = ref.current.getContext("2d");
    const labels = data.map(d => d.op);
    const isL = theme === "light";
    const tickColor = isL ? "#64748B" : "#94A3B8";
    const gridColor = isL ? "rgba(226, 232, 240, 0.8)" : "rgba(20,36,56,.9)";
    ch.current = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "20'",
          data: data.map(d => d.s20),
          backgroundColor: C.cyan + "CC",
          borderRadius: 3,
          barThickness: 14,
          maxBarThickness: 20
        }, {
          label: "40'",
          data: data.map(d => d.s40),
          backgroundColor: C.blue + "CC",
          borderRadius: 3,
          barThickness: 14,
          maxBarThickness: 20
        }, {
          label: "45'",
          data: data.map(d => d.s45),
          backgroundColor: C.teal + "CC",
          borderRadius: 3,
          barThickness: 14,
          maxBarThickness: 20
        }]
      },
      options: {
        indexAxis: 'x',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color: tickColor,
              boxWidth: 8,
              font: {
                size: 9
              },
              usePointStyle: true,
              padding: 12
            }
          },
          tooltip: {
            borderWidth: 1,
            borderColor: "var(--br)"
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9
              }
            }
          },
          y: {
            grid: {
              color: gridColor
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9
              }
            }
          }
        }
      }
    });
    return () => ch.current?.destroy();
  }, [data, theme]);
  return /*#__PURE__*/React.createElement("canvas", {
    ref: ref
  });
}
function QCBarChart({
  data,
  theme = "dark"
}) {
  const ref = useRef(null);
  const ch = useRef(null);
  useEffect(() => {
    if (!ref.current) return;
    ch.current?.destroy();
    const allVals = [...data.map(d => d.gmh), ...data.map(d => d.nmh)];
    const minV = Math.max(0, Math.floor(Math.min(...allVals) * 0.85));
    const maxV = Math.ceil(Math.max(...allVals) * 1.1);
    const isLight = theme === "light";
    const gridColor = isLight ? "rgba(226, 232, 240, 0.8)" : "rgba(20,36,56,.9)";
    const tickColor = isLight ? "#64748B" : "#3D556E";
    const legendColor = isLight ? "#475569" : "#5A748F";
    const ttBg = isLight ? "#FFFFFF" : "#121A2B";
    const ttBorder = isLight ? "#E2E8F0" : "#243048";
    const ttTitle = isLight ? "#0F172A" : "#E8EFF8";
    const ttBody = isLight ? "#334155" : "#8FA3BC";
    ch.current = new Chart(ref.current.getContext("2d"), {
      type: "bar",
      data: {
        labels: data.map(d => d.lbl || d.qc),
        datasets: [{
          label: "Gross M/h",
          data: data.map(d => d.gmh),
          backgroundColor: "rgba(59,130,246,.5)",
          borderColor: C.blue,
          borderWidth: 1,
          borderRadius: 3
        }, {
          label: "Net M/h",
          data: data.map(d => d.nmh),
          backgroundColor: "rgba(16,185,129,.5)",
          borderColor: C.green,
          borderWidth: 1,
          borderRadius: 3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: {
              color: legendColor,
              font: {
                size: 9.5,
                family: "Inter"
              },
              boxWidth: 10,
              padding: 10
            }
          },
          tooltip: {
            backgroundColor: ttBg,
            borderColor: ttBorder,
            borderWidth: 1,
            titleColor: ttTitle,
            bodyColor: ttBody
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9,
                family: "Inter"
              }
            }
          },
          y: {
            grid: {
              color: gridColor
            },
            border: {
              dash: [3, 3]
            },
            ticks: {
              color: tickColor,
              font: {
                size: 9,
                family: "Inter"
              }
            },
            min: minV,
            max: maxV
          }
        }
      }
    });
    return () => ch.current?.destroy();
  }, [data, theme]);
  return /*#__PURE__*/React.createElement("canvas", {
    ref: ref
  });
}
function DonutChart({
  data,
  theme = "dark",
  customColors = null,
  label = "Total"
}) {
  const ref = useRef(null);
  const ch = useRef(null);
  const groups = useMemo(() => {
    if (Array.isArray(data)) {
      const acc = {};
      data.forEach(d => {
        acc[d.type] = (acc[d.type] || 0) + d.dur;
      });
      return Object.entries(acc).map(([t, h]) => ({
        t,
        h: Math.round(h * 100) / 100
      }));
    } else {
      return Object.entries(data).map(([t, h]) => ({
        t,
        h
      }));
    }
  }, [data]);
  const clrs = customColors || {
    "Terminal Convenience": C.red,
    "Non-Terminal Convenience": C.amber,
    "Other/Force Majeure": C.purple
  };
  const total = groups.reduce((s, g) => s + g.h, 0);
  useEffect(() => {
    if (!ref.current) return;
    ch.current?.destroy();
    const isLight = theme === "light";
    const ttBg = isLight ? "#FFFFFF" : "#121A2B";
    const ttBorder = isLight ? "#E2E8F0" : "#243048";
    ch.current = new Chart(ref.current.getContext("2d"), {
      type: "doughnut",
      data: {
        labels: groups.map(g => g.t),
        datasets: [{
          data: groups.map(g => g.h),
          backgroundColor: groups.map(g => (clrs[g.t] || C.blue) + "BB"),
          borderColor: groups.map(g => clrs[g.t] || C.blue),
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "76%",
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: ttBg,
            borderColor: ttBorder,
            borderWidth: 1
          }
        }
      }
    });
    return () => ch.current?.destroy();
  }, [groups, theme, clrs]);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 20,
      alignItems: "center",
      justifyContent: "center",
      width: "100%"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      width: 154,
      height: 154,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("canvas", {
    ref: ref
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      inset: 0,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      pointerEvents: "none"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 22,
      fontWeight: 800,
      color: "var(--t1)"
    }
  }, total > 1000 ? (total / 1000).toFixed(1) + 'k' : total), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 8.5,
      color: "var(--t4)",
      marginTop: 2,
      textTransform: 'uppercase',
      letterSpacing: 0.5
    }
  }, label))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 100
    }
  }, groups.map(g => /*#__PURE__*/React.createElement("div", {
    key: g.t,
    className: "dl-i",
    style: {
      marginBottom: 4
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "dl-dot",
    style: {
      background: clrs[g.t] || C.blue,
      width: 7,
      height: 7
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "dl-lbl",
    style: {
      fontSize: 10.5,
      fontWeight: 500,
      width: 100,
      flex: "none"
    }
  }, g.t), /*#__PURE__*/React.createElement("div", {
    className: "dl-v",
    style: {
      fontSize: 11,
      fontWeight: 700,
      marginLeft: 10
    }
  }, g.h.toLocaleString())))));
}
function useMobile() {
  const [m, setM] = useState(() => window.innerWidth <= 768);
  useEffect(() => {
    const fn = () => setM(window.innerWidth <= 768);
    window.addEventListener('resize', fn);
    return () => window.removeEventListener('resize', fn);
  }, []);
  return m;
}
function KpiStrip({
  items
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "kpi-strip"
  }, items.map((k, i) => /*#__PURE__*/React.createElement(KpiCard, {
    key: i,
    ...k
  })));
}
function VesselAccordion({
  data,
  kt = 45
}) {
  const [open, setOpen] = useState(null);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px'
    }
  }, data.map(v => /*#__PURE__*/React.createElement("div", {
    key: v.id,
    className: "acc"
  }, /*#__PURE__*/React.createElement("div", {
    className: "acc-hd",
    onClick: () => setOpen(open === v.id ? null : v.id)
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      flexShrink: 0,
      background: v.nmph >= kt ? C.green : C.red
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12.5,
      fontWeight: 600,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, v.name), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--t3)',
      marginTop: 1
    }
  }, v.op, " · ", v.berth, " · ", v.voyage))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement(Sbadge, {
    s: v.st
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      color: v.nmph >= kt ? C.green : C.red,
      fontWeight: 700,
      fontSize: 13,
      fontFamily: 'var(--mono)'
    }
  }, v.nmph.toFixed(1)), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--t4)'
    }
  }, open === v.id ? '▲' : '▼'))), open === v.id && /*#__PURE__*/React.createElement("div", {
    className: "acc-bd"
  }, /*#__PURE__*/React.createElement("div", {
    className: "acc-grid"
  }, [['ATB', v.ata || '—'], ['ATD', v.atd || '—'], ['Portstay', v.portstay ? `${v.portstay.toFixed(1)}h` : '—'], ['Net Wk', `${v.net.toFixed(1)}h`], ['GMPH', v.gmph.toFixed(1)], ['NMPH', v.nmph.toFixed(1)], ['Discharge', v.dis], ['Load', v.load], ['Conts', v.conts], ['TEUs', v.teus], ['Cranes', v.cranes], ['CI', v.ci.toFixed(1)]].map(([k, val]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    className: "acc-cell"
  }, /*#__PURE__*/React.createElement("div", {
    className: "acc-cl"
  }, k), /*#__PURE__*/React.createElement("div", {
    className: "acc-cv",
    style: {
      color: k === 'NMPH' ? v.nmph >= kt ? C.green : C.red : 'var(--t1)'
    }
  }, val))))))));
}
function QCAccordion({
  data
}) {
  const [open, setOpen] = useState(null);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px'
    }
  }, data.map((q, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "acc"
  }, /*#__PURE__*/React.createElement("div", {
    className: "acc-hd",
    onClick: () => setOpen(open === i ? null : i)
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      flexShrink: 0,
      background: C.blue
    }
  }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 600
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--mono)',
      color: C.cyan
    }
  }, q.qc), " · ", q.vessel.split(' ')[0]), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--t3)',
      marginTop: 1
    }
  }, q.tot, " conts · ", q.dH.toFixed(1), "h delay"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 700,
      fontSize: 13,
      color: 'var(--t1)'
    }
  }, q.nmh.toFixed(1)), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--t4)'
    }
  }, open === i ? '▲' : '▼'))), open === i && /*#__PURE__*/React.createElement("div", {
    className: "acc-bd"
  }, /*#__PURE__*/React.createElement("div", {
    className: "acc-grid"
  }, [['Gross h', q.gH.toFixed(1)], ['Net h', q.nH.toFixed(1)], ['Delay h', q.dH.toFixed(1)], ['Total', q.tot], ['Gross M/h', q.gmh.toFixed(1)], ['Net M/h', q.nmh.toFixed(1)], ['Discharge', q.dis], ['Load', q.load]].map(([k, val]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    className: "acc-cell"
  }, /*#__PURE__*/React.createElement("div", {
    className: "acc-cl"
  }, k), /*#__PURE__*/React.createElement("div", {
    className: "acc-cv"
  }, val))))))));
}
function DelayAccordion({
  data
}) {
  const [open, setOpen] = useState(null);
  const sorted = [...data].sort((a, b) => b.dur - a.dur);
  const ec = {
    d: C.red,
    i: C.amber,
    m: C.purple,
    n: C.amber,
    a: C.red
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px'
    }
  }, sorted.map((d, i) => /*#__PURE__*/React.createElement("div", {
    key: d.id,
    className: "acc"
  }, /*#__PURE__*/React.createElement("div", {
    className: "acc-hd",
    onClick: () => setOpen(open === i ? null : i)
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      flexShrink: 0,
      background: ec[d.code] || C.red
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, d.vessel), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--t3)',
      marginTop: 1
    }
  }, d.qc, " · ", d.cat || '—', " · ", d.from, "–", d.to))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 7,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: d.dur >= 1 ? C.red : C.amber,
      fontWeight: 700,
      fontSize: 13
    }
  }, d.dur.toFixed(2), "h"), /*#__PURE__*/React.createElement(ErrCodeBadge, {
    code: d.code
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--t4)'
    }
  }, open === i ? '▲' : '▼'))), open === i && /*#__PURE__*/React.createElement("div", {
    className: "acc-bd"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--bg3)',
      borderRadius: 6,
      padding: '9px 11px',
      marginBottom: 6,
      fontSize: 11
    }
  }, /*#__PURE__*/React.createElement(Ebadge, {
    t: d.type
  })), /*#__PURE__*/React.createElement("div", {
    className: "acc-grid"
  }, [['QC', d.qc], ['Stop Cat.', d.cat || '—'], ['From', d.from], ['To', d.to], ['Duration', `${d.dur.toFixed(2)}h`]].map(([k, v]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    className: "acc-cell"
  }, /*#__PURE__*/React.createElement("div", {
    className: "acc-cl"
  }, k), /*#__PURE__*/React.createElement("div", {
    className: "acc-cv"
  }, v))))))));
}
const NAV = [{
  id: "overview",
  icon: "📊",
  lbl: "Operational Overview"
}, {
  id: "berth",
  icon: "🛳️",
  lbl: "Live Berth Status"
}, {
  id: "vessels",
  icon: "🚢",
  lbl: "Vessel Summary"
}, {
  id: "market",
  icon: "📈",
  lbl: "Market Analysis"
}, {
  id: "containers",
  icon: "📦",
  lbl: "Container Analysis"
}, {
  id: "cranes",
  icon: "🏗️",
  lbl: "QC Productivity"
}, {
  id: "operators",
  icon: "👥",
  lbl: "QC Operator Productivity"
}, {
  id: "delays",
  icon: "⏱️",
  lbl: "Delay & Downtime"
}, {
  id: "config",
  icon: "🛠️",
  lbl: "Config & Logs"
}];
const PT = {
  overview: "Operational Overview",
  berth: "Live Berth Status",
  vessels: "Vessel Performance",
  market: "Market Trend & Cargo Analysis",
  containers: "Container Status & Size Mix",
  cranes: "QC Productivity Analysis",
  operators: "QC Operator Productivity",
  delays: "Delay & Downtime Analysis",
  config: "Configuration & System Logs"
};
function MobileBottomNav({
  nav,
  setNav,
  delayCount = 0
}) {
  return /*#__PURE__*/React.createElement("nav", {
    className: "m-nav"
  }, NAV.map(n => /*#__PURE__*/React.createElement("div", {
    key: n.id,
    className: "m-nav-i",
    onClick: () => setNav(n.id),
    style: {
      color: nav === n.id ? C.blue : 'var(--t4)',
      background: nav === n.id ? 'rgba(59,130,246,.09)' : 'transparent'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 18,
      lineHeight: 1
    }
  }, n.icon), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9,
      fontWeight: nav === n.id ? 600 : 400
    }
  }, n.lbl.split(' ')[0]), n.id === "delays" && delayCount > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 4,
      right: 'calc(50% - 16px)',
      background: C.red,
      color: '#fff',
      fontSize: 7,
      fontWeight: 700,
      padding: '1px 4px',
      borderRadius: 8
    }
  }, delayCount))));
}
function MobilePages({
  nav,
  kpi,
  vessels,
  qcData,
  qcTimeline,
  berthStatus,
  delays,
  qcOpData = [],
  kt = 45,
  theme = "dark"
}) {
  const delta = kpi.avgNmph - kt;
  const sp = kpi.spark || SP0;
  const sec = (color, lbl) => /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '8px 10px 4px',
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: color
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11.5,
      fontWeight: 600,
      color: 'var(--t2)'
    }
  }, lbl));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      paddingBottom: 66
    }
  }, nav === "overview" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(KpiStrip, {
    items: [{
      lbl: "Vessels",
      val: kpi.tvs,
      ic: C.blue,
      icon: "⛵",
      dl: `${vessels.length} total`,
      dlt: "pos",
      spark: sp.v
    }, {
      lbl: "TEUs",
      val: kpi.tteus.toLocaleString(),
      ic: C.purple,
      icon: "📦",
      dl: "total",
      dlt: "pos",
      spark: sp.t
    }, {
      lbl: "Net M/h",
      val: kpi.avgNmph.toFixed(1),
      ic: delta >= 0 ? C.green : C.red,
      icon: "📈",
      dl: `${delta >= 0 ? "+" : ""}${delta.toFixed(1)} KPI`,
      dlt: delta >= 0 ? "pos" : "neg",
      spark: sp.nm
    }, {
      lbl: "Avg Delay",
      val: kpi.avgDly.toFixed(1),
      unit: "h",
      ic: C.red,
      icon: "⚠",
      dl: "per vessel",
      dlt: "neg",
      spark: sp.dl
    }, {
      lbl: "Portstay",
      val: kpi.avgPs.toFixed(1),
      unit: "h",
      ic: C.cyan,
      icon: "⚓",
      dl: "avg",
      dlt: "neu",
      spark: sp.ps
    }, {
      lbl: "Net Wk",
      val: kpi.avgNet.toFixed(1),
      unit: "h",
      ic: C.amber,
      icon: "⏱",
      dl: "avg",
      dlt: "neu",
      spark: sp.nw
    }]
  }), sec(C.cyan, "Live Berth Status"), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px 8px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      border: '1px solid var(--br2)',
      borderRadius: 8,
      overflow: 'hidden',
      padding: 8
    }
  }, /*#__PURE__*/React.createElement(BerthMap, {
    berths: berthStatus
  }))), sec(C.amber, "Vessel Operations — tap to expand"), /*#__PURE__*/React.createElement(VesselAccordion, {
    data: vessels,
    kt: kt
  })), nav === "vessels" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(KpiStrip, {
    items: [{
      lbl: "Total",
      val: vessels.length,
      ic: C.blue,
      icon: "⛵",
      dl: "vessels",
      dlt: "pos",
      spark: sp.v
    }, {
      lbl: "Berthed",
      val: vessels.filter(v => v.st === "Berthed").length,
      ic: C.green,
      icon: "⚓",
      dl: "Active",
      dlt: "neu",
      spark: sp.v
    }, {
      lbl: "Completed",
      val: vessels.filter(v => v.st === "Completed").length,
      ic: C.cyan,
      icon: "✓",
      dl: "Today",
      dlt: "pos",
      spark: sp.v
    }, {
      lbl: "TEUs",
      val: kpi.tteus.toLocaleString(),
      ic: C.purple,
      icon: "📦",
      dl: "total",
      dlt: "pos",
      spark: sp.t
    }]
  }), /*#__PURE__*/React.createElement(VesselAccordion, {
    data: vessels,
    kt: kt
  })), nav === "cranes" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(KpiStrip, {
    items: [{
      lbl: "Active QC",
      val: qcTimeline.length,
      ic: C.blue,
      icon: "⚙",
      dl: "cranes",
      dlt: "neu",
      spark: sp.v
    }, {
      lbl: "Avg Net M/h",
      val: qcData.length ? (qcData.reduce((s, q) => s + q.nmh, 0) / qcData.length).toFixed(1) : "—",
      ic: C.green,
      icon: "📈",
      dl: "vs KPI",
      dlt: "pos",
      spark: sp.nm
    }, {
      lbl: "Above KPI",
      val: `${qcData.filter(q => q.nmh >= kt).length}/${qcData.length}`,
      ic: C.green,
      icon: "✓",
      dl: "passing",
      dlt: "pos",
      spark: sp.v
    }, {
      lbl: "Avg Delay",
      val: qcData.length ? (qcData.reduce((s, q) => s + q.dH, 0) / qcData.length).toFixed(1) : "—",
      unit: "h",
      ic: C.amber,
      icon: "⏱",
      dl: "per crane",
      dlt: "neg",
      spark: sp.dl
    }]
  }), sec(C.cyan, "Crane Assignment Timeline"), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px 8px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--bg2)',
      border: '1px solid var(--br2)',
      borderRadius: 8,
      overflowX: 'auto',
      padding: '10px 12px'
    }
  }, /*#__PURE__*/React.createElement(QCGantt, {
    timeline: qcTimeline
  }))), sec(C.green, "QC Detail Records"), /*#__PURE__*/React.createElement(QCAccordion, {
    data: qcData,
    kt: kt
  })), nav === "operators" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(KpiStrip, {
    items: [{
      lbl: "Active QC",
      val: new Set(qcOpData.map(q => q.qc)).size,
      ic: C.blue,
      icon: "⚙",
      dl: "cranes",
      dlt: "neu",
      spark: sp.v
    }, {
      lbl: "Avg Net M/h",
      val: qcOpData.length ? (qcOpData.reduce((s, q) => s + q.nmh, 0) / qcOpData.length).toFixed(1) : "—",
      ic: C.green,
      icon: "📈",
      dl: "vs KPI",
      dlt: "pos",
      spark: sp.nm
    }, {
      lbl: "Above KPI",
      val: `${qcOpData.filter(q => q.nmh >= kt).length}/${qcOpData.length}`,
      ic: C.green,
      icon: "✓",
      dl: "passing",
      dlt: "pos",
      spark: sp.v
    }, {
      lbl: "Avg Delay",
      val: qcOpData.length ? (qcOpData.reduce((s, q) => s + q.dH, 0) / qcOpData.length).toFixed(1) : "—",
      unit: "h",
      ic: C.amber,
      icon: "⏱",
      dl: "per crane",
      dlt: "neg",
      spark: sp.dl
    }]
  }), sec(C.green, "QC Operator Detail Records (Adjusted)"), /*#__PURE__*/React.createElement(QCAccordion, {
    data: qcOpData,
    kt: kt
  })), nav === "delays" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(KpiStrip, {
    items: [{
      lbl: "Events",
      val: delays.length,
      ic: C.red,
      icon: "⚠",
      dl: "total",
      dlt: "neg",
      spark: sp.de
    }, {
      lbl: "Total Hrs",
      val: kpi.tdHrs.toFixed(1),
      unit: "h",
      ic: C.amber,
      icon: "⏱",
      dl: "total",
      dlt: "neg",
      spark: sp.dh
    }, {
      lbl: "Terminal %",
      val: `${kpi.tcPct}%`,
      ic: C.purple,
      icon: "⚡",
      dl: "of delays",
      dlt: "pos",
      spark: sp.de
    }, {
      lbl: "Avg/Vessel",
      val: kpi.avgDly.toFixed(1),
      unit: "h",
      ic: C.green,
      icon: "📉",
      dl: "per vessel",
      dlt: "pos",
      spark: sp.dl
    }]
  }), sec(C.red, "Delay Breakdown"), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px 8px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--bg2)',
      border: '1px solid var(--br2)',
      borderRadius: 8,
      padding: '12px'
    }
  }, /*#__PURE__*/React.createElement(DonutChart, {
    data: delays,
    theme: theme
  }))), sec(C.amber, "Delay Timeline"), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px 8px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--bg2)',
      border: '1px solid var(--br2)',
      borderRadius: 8,
      overflowX: 'auto',
      padding: '10px 12px'
    }
  }, /*#__PURE__*/React.createElement(DelayGantt, {
    data: delays
  }))), sec(C.red, "Delay Events"), /*#__PURE__*/React.createElement(DelayAccordion, {
    data: delays
  })), nav === "market" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(KpiStrip, {
    items: [{
      lbl: "Total Moves",
      val: Object.values(marketStats.cargo).reduce((a, b) => a + b, 0),
      ic: C.blue,
      icon: "📦",
      dl: "filtered",
      dlt: "pos",
      spark: sp.t
    }, {
      lbl: "Imp Ratio",
      val: `${Math.round((marketStats.cargo.Discharge || 0) / (Object.values(marketStats.cargo).reduce((a, b) => a + b, 0) || 1) * 100)}%`,
      ic: C.cyan,
      icon: "📉",
      dl: "discharge",
      dlt: "pos",
      spark: sp.t
    }]
  }), sec(C.blue, "Cargo Mix (Discharge/Load)"), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px 8px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--bg2)',
      border: '1px solid var(--br2)',
      borderRadius: 8,
      padding: '12px'
    }
  }, /*#__PURE__*/React.createElement(DonutChart, {
    data: marketStats.cargo,
    theme: theme,
    customColors: {
      "Discharge": C.blue,
      "Load": C.green,
      "Shifting": C.purple
    },
    label: "Moves"
  }))), sec(C.cyan, "Market Volume Trend"), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px 8px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--bg2)',
      border: '1px solid var(--br2)',
      borderRadius: 8,
      padding: '12px',
      height: 200
    }
  }, /*#__PURE__*/React.createElement(MarketTrendChart, {
    data: marketStats.trends,
    theme: theme
  })))), nav === "containers" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(KpiStrip, {
    items: [{
      lbl: "Full %",
      val: `${Math.round(marketStats.status.Full / (marketStats.status.Full + marketStats.status.Empty || 1) * 100)}%`,
      ic: C.purple,
      icon: "⚡",
      dl: "laden",
      dlt: "pos",
      spark: sp.t
    }, {
      lbl: "40' Ratio",
      val: `${Math.round(marketStats.size["40'"] / (Object.values(marketStats.size).reduce((a, b) => a + b, 0) || 1) * 100)}%`,
      ic: C.green,
      icon: "📏",
      dl: "large units",
      dlt: "pos",
      spark: sp.t
    }]
  }), sec(C.purple, "Full vs Empty Status"), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px 8px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--bg2)',
      border: '1px solid var(--br2)',
      borderRadius: 8,
      padding: '12px'
    }
  }, /*#__PURE__*/React.createElement(DonutChart, {
    data: marketStats.status,
    theme: theme,
    customColors: {
      "Full": C.purple,
      "Empty": "#3D556E"
    },
    label: "Total"
  }))), sec(C.cyan, "Container Size Distribution"), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 10px 8px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--bg2)',
      border: '1px solid var(--br2)',
      borderRadius: 8,
      padding: '12px'
    }
  }, /*#__PURE__*/React.createElement(DonutChart, {
    data: marketStats.size,
    theme: theme,
    label: "Size"
  })))), nav === "config" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(KpiStrip, {
    items: [{
      lbl: "API",
      val: "OK",
      ic: C.green,
      icon: "✓",
      dl: "Healthy",
      dlt: "pos",
      spark: [1, 1, 1, 1, 1, 1, 1, 1]
    }, {
      lbl: "KPI Target",
      val: kt,
      unit: "M/h",
      ic: C.blue,
      icon: "🎯",
      dl: "target",
      dlt: "neu",
      spark: Array(8).fill(kt)
    }, {
      lbl: "Records",
      val: `${vessels.length}·${qcData.length}`,
      ic: C.purple,
      icon: "🗄",
      dl: "v·qc",
      dlt: "neu",
      spark: sp.v
    }, {
      lbl: "Last Load",
      val: new Date().toLocaleTimeString('en', {
        hour: '2-digit',
        minute: '2-digit'
      }),
      ic: C.cyan,
      icon: "⏱",
      dl: "success",
      dlt: "pos",
      spark: [1, 1, 1, 1, 1, 1, 1, 1]
    }]
  })));
}

/* ═══════════ App ═══════════════════════════════════════════════════════════ */
function App() {
  const isMobile = useMobile();
  const getUrlParam = key => new URLSearchParams(window.location.search).get(key) || "";
  const [nav, setNavState] = useState(() => getUrlParam("tab") || "overview");
  const [col, setCol] = useState(false);
  const [notif, setNotif] = useState(false);
  const [uprof, setUprof] = useState(false);
  const [userName, setUserNameState] = useState(() => localStorage.getItem("tdr_user_name") || "Vân Trình");
  const [userRole, setUserRoleState] = useState(() => localStorage.getItem("tdr_user_role") || "System Admin");
  const [showSettings, setShowSettings] = useState(false);
  const setUserName = v => {
    setUserNameState(v);
    localStorage.setItem("tdr_user_name", v);
  };
  const setUserRole = v => {
    setUserRoleState(v);
    localStorage.setItem("tdr_user_role", v);
  };
  const userInitials = useMemo(() => {
    const parts = userName.split(" ");
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    return userName.slice(0, 2).toUpperCase();
  }, [userName]);
  const [feed, setFeed] = useState(false);
  const [opTab, setOpTab] = useState("MTD");
  const [qcPg, setQcPg] = useState(0);
  const [selectedCrane, setSelectedCrane] = useState("ALL");
  const [craneGroupBy, setCraneGroupBy] = useState("day");
  const [logFilter, setLogFilter] = useState("ALL");
  const [apiData, setApiData] = useState(null);
  const [apiLoading, setApiLoading] = useState(true);
  const [apiError, setApiError] = useState(null);
  const [fDateFrom, setFDateFromState] = useState(() => getUrlParam("from") || "");
  const [fDateTo, setFDateToState] = useState(() => getUrlParam("to") || "");
  const [fOp, setFOpState] = useState(() => getUrlParam("op") || "");
  const [fBerth, setFBerthState] = useState(() => getUrlParam("berth") || "");
  const [fVessel, setFVesselState] = useState(() => getUrlParam("vessel") || "");
  const [trendMode, setTrendMode] = useState("Weekly");
  const setNav = v => {
    setNavState(v);
    setQcPg(0);
  };
  const setFDateFrom = v => {
    setFDateFromState(v);
    setQcPg(0);
  };
  const setFDateTo = v => {
    setFDateToState(v);
    setQcPg(0);
  };
  const setFOp = v => {
    setFOpState(v);
    setQcPg(0);
  };
  const setFBerth = v => {
    setFBerthState(v);
    setQcPg(0);
  };
  const setFVessel = v => {
    setFVesselState(v);
    setQcPg(0);
  };
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (nav && nav !== "overview") params.set("tab", nav);else params.delete("tab");
    if (fDateFrom) params.set("from", fDateFrom);else params.delete("from");
    if (fDateTo) params.set("to", fDateTo);else params.delete("to");
    if (fOp) params.set("op", fOp);else params.delete("op");
    if (fBerth) params.set("berth", fBerth);else params.delete("berth");
    if (fVessel) params.set("vessel", fVessel);else params.delete("vessel");
    params.delete("token");
    const newQuery = params.toString();
    const newUrl = window.location.pathname + (newQuery ? "?" + newQuery : "");
    window.history.replaceState({}, document.title, newUrl);
  }, [nav, fDateFrom, fDateTo, fOp, fBerth, fVessel]);
  const [filtOpen, setFiltOpen] = useState(true);
  const [theme, setTheme] = useState(() => localStorage.getItem("tdr_theme") || "dark");
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("tdr_theme", theme);
  }, [theme]);

  // Persistent Custom KPI Target
  const [customKt, setCustomKtState] = useState(() => {
    const saved = localStorage.getItem("tdr_kpi_target");
    return saved ? parseInt(saved, 10) : null;
  });
  const setCustomKt = val => {
    setCustomKtState(val);
    if (val !== null) {
      localStorage.setItem("tdr_kpi_target", val);
    } else {
      localStorage.removeItem("tdr_kpi_target");
    }
  };
  const getApiToken = useCallback(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get("token");
    if (urlToken) {
      localStorage.setItem("tdr_api_token", urlToken);
      params.delete("token");
      const newQuery = params.toString();
      const newUrl = window.location.pathname + (newQuery ? "?" + newQuery : "");
      window.history.replaceState({}, document.title, newUrl);
      return urlToken;
    }
    return localStorage.getItem("tdr_api_token") || "";
  }, []);

  // silent=true → background refresh (no loading flash); silent=false → initial load
  const reloadData = useCallback((silent = false) => {
    if (!silent) {
      setApiLoading(true);
      setApiError(null);
    }
    const token = getApiToken();
    fetch("/api/data", {
      headers: {
        "X-API-Token": token
      }
    }).then(r => {
      if (r.status === 401) {
        localStorage.removeItem("tdr_api_token");
        throw new Error("UNAUTHORIZED");
      }
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    }).then(d => {
      setApiData(d);
      if (!silent) setApiLoading(false);
    }).catch(e => {
      if (!silent || String(e).includes("UNAUTHORIZED")) {
        setApiError(String(e));
        setApiLoading(false);
      }
    });
  }, [getApiToken]);

  // Auto-refresh every 30s — silent mode (no loading flash)
  useEffect(() => {
    const interval = setInterval(() => {
      if (!apiLoading && apiError !== "Error: UNAUTHORIZED") {
        reloadData(true); // silent background refresh
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [reloadData, apiLoading, apiError]);
  useEffect(() => {
    reloadData();
  }, [reloadData]);

  // Sprint 2-6: Client-side CSV export logic
  const exportToCSV = useCallback((data, filename) => {
    if (!data || data.length === 0) return;
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(",")];
    for (const row of data) {
      const values = headers.map(header => {
        let val = row[header];
        if (val === null || val === undefined) val = '';
        const escaped = ('' + val).replace(/"/g, '""');
        return `"${escaped}"`;
      });
      csvRows.push(values.join(","));
    }
    const blob = new Blob([csvRows.join("\r\n")], {
      type: 'text/csv;charset=utf-8;'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `${filename}_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, []);
  const allDates = useMemo(() => {
    const dates = new Set();
    if (apiData?.meta?.reportDate) dates.add(apiData.meta.reportDate);
    (apiData?.vessels ?? []).forEach(v => {
      if (v.ata) {
        const d = v.ata.split(" ")[0];
        if (/^\d{4}-\d{2}-\d{2}$/.test(d)) dates.add(d);
      }
    });
    return Array.from(dates).sort();
  }, [apiData]);
  const dateMin = allDates[0] || "";
  const dateMax = allDates[allDates.length - 1] || "";
  const allOps = useMemo(() => {
    const ops = new Set();
    (apiData?.vessels ?? []).forEach(v => {
      if (v.op) ops.add(v.op);
    });
    return Array.from(ops).sort();
  }, [apiData]);
  const allBerths = useMemo(() => {
    const bs = new Set();
    (apiData?.vessels ?? []).forEach(v => {
      if (v.berth) bs.add(v.berth);
    });
    (apiData?.berths ?? []).forEach(b => {
      if (b.id) bs.add(b.id);
    });
    return Array.from(bs).sort();
  }, [apiData]);
  const allVessels = useMemo(() => {
    const vs = new Set();
    (apiData?.vessels ?? []).forEach(v => {
      if (v.name) vs.add(v.name);
    });
    return Array.from(vs).sort();
  }, [apiData]);
  const vessels = useMemo(() => {
    let res = apiData?.vessels ?? [];
    if (fDateFrom || fDateTo) res = res.filter(v => {
      if (!v.ata) return false;
      const d = v.ata.split(" ")[0];
      if (fDateFrom && d < fDateFrom) return false;
      if (fDateTo && d > fDateTo) return false;
      return true;
    });
    if (fOp) res = res.filter(v => v.op === fOp);
    if (fBerth) res = res.filter(v => v.berth === fBerth);
    if (fVessel) res = res.filter(v => v.name === fVessel);
    return res;
  }, [apiData, fDateFrom, fDateTo, fOp, fBerth, fVessel]);
  const delays = useMemo(() => {
    let res = apiData?.delays ?? [];
    const activeVesselNames = new Set(vessels.map(v => v.name));
    res = res.filter(d => activeVesselNames.has(d.vessel));
    if (fBerth) {
      res = res.filter(d => {
        const v = vessels.find(x => x.name === d.vessel);
        return v && v.berth === fBerth;
      });
    }
    return res;
  }, [apiData, vessels, fBerth]);
  const qcData = useMemo(() => {
    let res = apiData?.qc ?? [];
    const activeVesselNames = new Set(vessels.map(v => v.name));
    res = res.filter(q => activeVesselNames.has(q.vessel));
    return res;
  }, [apiData, vessels]);
  const qcTimeline = useMemo(() => {
    let res = apiData?.qcTimeline ?? [];
    const activeVesselNames = new Set(vessels.map(v => v.name));
    res = res.map(row => {
      const segs = row.segs.filter(seg => activeVesselNames.has(seg.v));
      return {
        ...row,
        segs
      };
    }).filter(row => row.segs.length > 0);
    return res;
  }, [apiData, vessels]);
  const berthStatus = useMemo(() => {
    let res = apiData?.berths ?? [];
    const activeVesselNames = new Set(vessels.map(v => v.name));
    return res.map(b => {
      if (b.vessel && !activeVesselNames.has(b.vessel)) {
        return {
          ...b,
          vessel: null,
          op: null,
          cranes: 0,
          pct: 0,
          conts: 0,
          atb: null,
          status: "Available"
        };
      }
      return b;
    });
  }, [apiData, vessels]);

  // --- Granular Market & Container Analysis Filtering ---
  const marketData = useMemo(() => {
    let res = apiData?.market ?? [];
    if (fDateFrom || fDateTo) res = res.filter(m => {
      if (!m["Report Date"]) return false;
      if (fDateFrom && m["Report Date"] < fDateFrom) return false;
      if (fDateTo && m["Report Date"] > fDateTo) return false;
      return true;
    });
    if (fOp) res = res.filter(m => m["Operator"] === fOp);
    if (fVessel) res = res.filter(m => m["Vessel Name"] === fVessel);
    return res;
  }, [apiData, fDateFrom, fDateTo, fOp, fVessel]);
  const marketStats = useMemo(() => {
    if (!marketData.length) return {
      cargo: {},
      status: {},
      size: {},
      trends: [],
      byOp: [],
      byVessel: []
    };
    const cargo = {};
    const status = {
      Full: 0,
      Empty: 0
    };
    const size = {
      "20'": 0,
      "40'": 0,
      "45'": 0
    };
    const trendsRaw = {};
    const ops = {};
    const vsls = {};
    marketData.forEach(m => {
      const opType = m.OperationType || "Unknown";
      const op = m.Operator || "Unknown";
      const v = m["Vessel Name"] || "Unknown";
      const total = m["Total Conts"] || 0;
      const full = m.Full || 0;
      const empty = m.Empty || 0;
      const s20 = m.s20 || 0;
      const s40 = m.s40 || 0;
      const s45 = m.s45 || 0;
      cargo[opType] = (cargo[opType] || 0) + total;
      status.Full += full;
      status.Empty += empty;
      size["20'"] += s20;
      size["40'"] += s40;
      size["45'"] += s45;

      // Operator summary
      if (!ops[op]) ops[op] = {
        op,
        total: 0,
        dis: 0,
        load: 0,
        full: 0,
        empty: 0,
        s20: 0,
        s40: 0,
        s45: 0
      };
      ops[op].total += total;
      ops[op].full += full;
      ops[op].empty += empty;
      ops[op].s20 += s20;
      ops[op].s40 += s40;
      ops[op].s45 += s45;
      if (opType === "Discharge") ops[op].dis += total;else if (opType === "Load" || opType === "Loading") ops[op].load += total;

      // Vessel summary
      if (!vsls[v]) vsls[v] = {
        v,
        total: 0,
        dis: 0,
        load: 0,
        full: 0,
        empty: 0,
        s20: 0,
        s40: 0,
        s45: 0
      };
      vsls[v].total += total;
      vsls[v].full += full;
      vsls[v].empty += empty;
      vsls[v].s20 += s20;
      vsls[v].s40 += s40;
      vsls[v].s45 += s45;
      if (opType === "Discharge") vsls[v].dis += total;else if (opType === "Load" || opType === "Loading") vsls[v].load += total;
      const dt = m["Report Date"];
      if (dt) trendsRaw[dt] = (trendsRaw[dt] || 0) + total;
    });
    const trends = Object.entries(trendsRaw).sort(([a], [b]) => a.localeCompare(b)).map(([date, volume]) => ({
      date,
      volume
    })).slice(-12);

    // Monthly trend aggregation
    const monthlyRaw = {};
    Object.entries(trendsRaw).forEach(([date, volume]) => {
      const month = date.substring(0, 7); // "YYYY-MM"
      monthlyRaw[month] = (monthlyRaw[month] || 0) + volume;
    });
    const trendsMonthly = Object.entries(monthlyRaw).sort(([a], [b]) => a.localeCompare(b)).map(([date, volume]) => ({
      date,
      volume
    })).slice(-6);
    const byOp = Object.values(ops).sort((a, b) => b.total - a.total);
    const byVessel = Object.values(vsls).sort((a, b) => b.total - a.total);
    return {
      cargo,
      status,
      size,
      trends,
      trendsMonthly,
      byOp,
      byVessel
    };
  }, [marketData]);
  const operators = apiData?.operators ?? [];
  const sp = apiData?.spark ?? SP0;
  const feedLines = apiData?.feed ?? [];
  const kt = customKt !== null ? customKt : apiData?.meta?.kpiTarget ?? 45;
  const reportDate = apiData?.meta?.reportDate ?? "";
  const dbStatus = apiData?.meta?.dbStatus ?? "unknown";
  const metaVer = apiData?.meta?.version ?? "v1.0.0";
  KPI_TARGET = kt;
  const kpi = useMemo(() => {
    const tvs = vessels.length || 0;
    if (tvs === 0) return {
      tvs: 0,
      tteus: 0,
      avgPs: 0,
      avgNet: 0,
      avgNmph: 0,
      tdHrs: 0,
      avgDly: 0,
      above: 0,
      tcPct: 0,
      reportDate,
      spark: sp
    };
    const tteus = vessels.reduce((s, v) => s + (v.teus || 0), 0);
    const comp = vessels.filter(v => v.portstay);
    const avgPs = comp.length ? comp.reduce((s, v) => s + (v.portstay || 0), 0) / comp.length : 0;
    const avgNet = vessels.reduce((s, v) => s + (v.net || 0), 0) / tvs;
    const avgNmph = vessels.reduce((s, v) => s + (v.nmph || 0), 0) / tvs;
    const tdHrs = delays.reduce((s, d) => s + (d.dur || 0), 0);
    const avgDly = tvs ? tdHrs / tvs : 0;
    const above = vessels.filter(v => (v.nmph || 0) >= kt).length;
    const termHrs = delays.filter(d => d.type === "Terminal Convenience").reduce((s, d) => s + (d.dur || 0), 0);
    const tcPct = tdHrs > 0 ? Math.round(termHrs / tdHrs * 100) : 0;
    return {
      tvs,
      tteus,
      avgPs,
      avgNet,
      avgNmph,
      tdHrs,
      avgDly,
      above,
      tcPct,
      reportDate,
      spark: sp
    };
  }, [vessels, delays, kt, sp, reportDate]);
  const activeFiltersCount = (fDateFrom || fDateTo ? 1 : 0) + (fOp ? 1 : 0) + (fBerth ? 1 : 0) + (fVessel ? 1 : 0);
  const moveDelta = kpi.avgNmph - kt;
  const NOTIFS = vessels.filter(v => (v.nmph || 0) < kt).slice(0, 5).map(v => ({
    t: `KPI Alert — ${v.name}`,
    s: `Net M/h: ${(v.nmph || 0).toFixed(1)} vs target ${kt}`,
    c: (v.nmph || 0) < kt - 1 ? C.red : C.amber
  }));

  /* Delay tab: per-vessel summary */
  const vesselDelayMap = useMemo(() => {
    const m = {};
    delays.forEach(d => {
      if (!m[d.vessel]) m[d.vessel] = {
        vessel: d.vessel,
        total: 0,
        terminal: 0,
        nonTerminal: 0,
        force: 0,
        events: 0,
        critical: 0
      };
      const r = m[d.vessel];
      r.total += d.dur;
      r.events++;
      if (d.dur >= 1) r.critical++;
      if (d.type === "Terminal Convenience") r.terminal += d.dur;else if (d.type === "Non-Terminal Convenience") r.nonTerminal += d.dur;else r.force += d.dur;
    });
    return Object.values(m).sort((a, b) => b.total - a.total);
  }, [delays]);

  /* Crane tab: Gross/Net grouped by date period */
  const filteredQc = useMemo(() => selectedCrane === "ALL" ? qcData : qcData.filter(q => q.qc === selectedCrane), [qcData, selectedCrane]);
  const groupedChartData = useMemo(() => {
    const buckets = {};
    filteredQc.forEach(q => {
      const matchV = vessels.find(v => v.name === q.vessel);
      const ataRaw = matchV?.ata || "";
      let dateStr = ataRaw.split(" ")[0] || "";
      if (!dateStr.includes("-")) {
        dateStr = reportDate.split(" ")[0] || "";
      }
      if (!dateStr) return;
      let key = dateStr;
      if (craneGroupBy === "week") {
        const d = new Date(dateStr);
        const day = d.getDay();
        const mon = new Date(d);
        mon.setDate(d.getDate() - day + 1);
        key = "W/" + mon.toISOString().slice(0, 10);
      } else if (craneGroupBy === "month") {
        key = dateStr.slice(0, 7);
      } else if (craneGroupBy === "quarter") {
        const m = parseInt(dateStr.slice(5, 7));
        key = dateStr.slice(0, 4) + "-Q" + Math.ceil(m / 3);
      }
      if (!buckets[key]) buckets[key] = {
        gmhS: 0,
        nmhS: 0,
        cnt: 0
      };
      buckets[key].gmhS += q.gmh;
      buckets[key].nmhS += q.nmh;
      buckets[key].cnt++;
    });
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return Object.entries(buckets).sort(([a], [b]) => a.localeCompare(b)).map(([k, v]) => {
      let displayLabel = k;
      try {
        if (craneGroupBy === "day") {
          const p = k.split("-");
          if (p.length === 3) displayLabel = `${p[2]} ${months[parseInt(p[1]) - 1]} ${p[0]}`;
        } else if (craneGroupBy === "week") {
          const dateStr = k.replace("W/", "");
          const p = dateStr.split("-");
          if (p.length === 3) displayLabel = `Wk of ${p[2]} ${months[parseInt(p[1]) - 1]} ${p[0]}`;
        } else if (craneGroupBy === "month") {
          const p = k.split("-");
          if (p.length === 2) displayLabel = `${months[parseInt(p[1]) - 1]} ${p[0]}`;
        } else if (craneGroupBy === "quarter") {
          const p = k.split("-Q");
          if (p.length === 2) displayLabel = `Q${p[1]} ${p[0]}`;
        }
      } catch (e) {
        displayLabel = k;
      }
      return {
        lbl: displayLabel,
        gmh: v.cnt ? v.gmhS / v.cnt : 0,
        nmh: v.cnt ? v.nmhS / v.cnt : 0
      };
    });
  }, [filteredQc, craneGroupBy, vessels]);
  const qcOpData = useMemo(() => {
    let res = apiData?.qcOperator ?? [];
    const activeVesselNames = new Set(vessels.map(v => v.name));
    res = res.filter(q => activeVesselNames.has(q.vessel));
    return res;
  }, [apiData, vessels]);
  const filteredQcOp = useMemo(() => {
    return selectedCrane === "ALL" ? qcOpData : qcOpData.filter(q => q.qc === selectedCrane);
  }, [qcOpData, selectedCrane]);
  const groupedChartDataOp = useMemo(() => {
    const buckets = {};
    filteredQcOp.forEach(q => {
      const matchV = vessels.find(v => v.name === q.vessel);
      const ataRaw = matchV?.ata || "";
      let dateStr = ataRaw.split(" ")[0] || "";
      if (!dateStr.includes("-")) {
        dateStr = reportDate.split(" ")[0] || "";
      }
      if (!dateStr) return;
      let key = dateStr;
      if (craneGroupBy === "week") {
        const d = new Date(dateStr);
        const day = d.getDay();
        const mon = new Date(d);
        mon.setDate(d.getDate() - day + 1);
        key = "W/" + mon.toISOString().slice(0, 10);
      } else if (craneGroupBy === "month") {
        key = dateStr.slice(0, 7);
      } else if (craneGroupBy === "quarter") {
        const m = parseInt(dateStr.slice(5, 7));
        key = dateStr.slice(0, 4) + "-Q" + Math.ceil(m / 3);
      }
      if (!buckets[key]) buckets[key] = {
        gmhS: 0,
        nmhS: 0,
        cnt: 0
      };
      buckets[key].gmhS += q.gmh;
      buckets[key].nmhS += q.nmh;
      buckets[key].cnt++;
    });
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return Object.entries(buckets).sort(([a], [b]) => a.localeCompare(b)).map(([k, v]) => {
      let displayLabel = k;
      try {
        if (craneGroupBy === "day") {
          const p = k.split("-");
          if (p.length === 3) displayLabel = `${p[2]} ${months[parseInt(p[1]) - 1]} ${p[0]}`;
        } else if (craneGroupBy === "week") {
          const dateStr = k.replace("W/", "");
          const p = dateStr.split("-");
          if (p.length === 3) displayLabel = `Wk of ${p[2]} ${months[parseInt(p[1]) - 1]} ${p[0]}`;
        } else if (craneGroupBy === "month") {
          const p = k.split("-");
          if (p.length === 2) displayLabel = `${months[parseInt(p[1]) - 1]} ${p[0]}`;
        } else if (craneGroupBy === "quarter") {
          const p = k.split("-Q");
          if (p.length === 2) displayLabel = `Q${p[1]} ${p[0]}`;
        }
      } catch (e) {
        displayLabel = k;
      }
      return {
        lbl: displayLabel,
        gmh: v.cnt ? v.gmhS / v.cnt : 0,
        nmh: v.cnt ? v.nmhS / v.cnt : 0
      };
    });
  }, [filteredQcOp, craneGroupBy, vessels]);
  const getHeaderSubtitle = () => {
    if (!apiData) return "Loading...";
    const activeCranesCount = new Set(filteredQcOp.map(q => q.qc)).size;
    const critCount = delays.filter(d => d.dur >= 1).length;
    const belowKpiCount = vessels.filter(v => (v.nmph || 0) < kt).length;
    switch (nav) {
      case "overview":
        return `${reportDate || "—"} · ${vessels.length} vessels · ${kpi.above}/${kpi.tvs} above KPI`;
      case "vessels":
        return `${vessels.length} vessels · ${vessels.filter(v => v.st === "Berthed").length} berthed · ${vessels.filter(v => v.st === "Completed").length} completed · ${belowKpiCount} below KPI`;
      case "cranes":
        return `${filteredQc.length} records · ${qcTimeline.length} active cranes`;
      case "operators":
        return `${filteredQcOp.length} records · ${activeCranesCount} cranes · Adjusted Net M/h`;
      case "delays":
        return `${delays.length} events · ${new Set(delays.map(d => d.vessel)).size} vessels · ${critCount} critical (≥1h)`;
      case "config":
        return `Flask ${metaVer} · SQLite · ${dbStatus}`;
      default:
        return `${reportDate || "—"} · ${vessels.length} vessels`;
    }
  };
  if (apiLoading) return /*#__PURE__*/React.createElement("div", {
    style: {
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
      background: "var(--bg0)"
    }
  }, /*#__PURE__*/React.createElement("header", {
    className: "hdr"
  }, /*#__PURE__*/React.createElement("div", {
    className: "logo",
    style: {
      background: "white",
      padding: "2px"
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "assets/csg-logo.jpg",
    alt: "CSG",
    style: {
      width: "100%",
      height: "100%",
      objectFit: "contain",
      display: "block",
      borderRadius: "4px"
    },
    onError: e => {
      e.target.style.display = 'none';
      e.target.parentElement.style.background = 'linear-gradient(135deg, #3B82F6, #0EA5E9)';
      e.target.parentElement.style.padding = '0';
      e.target.parentElement.innerHTML = 'TDR';
    }
  })), /*#__PURE__*/React.createElement("div", {
    className: "hdr-t"
  }, /*#__PURE__*/React.createElement("h2", null, "TDR Processor"), /*#__PURE__*/React.createElement("p", null, "Connecting…"))), /*#__PURE__*/React.createElement("div", {
    className: "ld-wrap"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ld-spin"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11
    }
  }, "Loading dashboard data…")));
  if (apiError === "Error: UNAUTHORIZED") return /*#__PURE__*/React.createElement("div", {
    style: {
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
      background: "var(--bg0)",
      justifyContent: "center",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("header", {
    className: "hdr",
    style: {
      position: "absolute",
      top: 0,
      left: 0,
      right: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "logo",
    style: {
      background: "rgba(59,130,246,.2)",
      color: C.blue
    }
  }, "🔑"), /*#__PURE__*/React.createElement("div", {
    className: "hdr-t"
  }, /*#__PURE__*/React.createElement("h2", null, "TDR Processor"), /*#__PURE__*/React.createElement("p", null, "Authentication Required"))), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      width: 380,
      padding: 28,
      textAlign: "center",
      borderRadius: 12,
      boxShadow: "0 10px 30px rgba(0,0,0,.35)",
      border: "1px solid var(--br2)",
      background: "var(--bg1)",
      marginTop: 40
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 28,
      marginBottom: 12
    }
  }, "🔒"), /*#__PURE__*/React.createElement("h2", {
    style: {
      color: "var(--t1)",
      fontSize: 18,
      fontWeight: 700,
      marginBottom: 8
    }
  }, "Enter Access Token"), /*#__PURE__*/React.createElement("p", {
    style: {
      color: "var(--t3)",
      fontSize: 11.5,
      lineHeight: "1.5",
      marginBottom: 20
    }
  }, "This dashboard is secured. Enter your TDR API Access Token below to unlock real-time terminal metrics."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 12,
      alignItems: "stretch"
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "password",
    placeholder: "API Access Token...",
    id: "tokenInput",
    style: {
      background: "var(--bg0)",
      border: "1px solid var(--br2)",
      padding: "10px 14px",
      borderRadius: 8,
      color: "var(--t1)",
      fontSize: 13,
      textAlign: "center",
      outline: "none",
      fontFamily: "var(--mono)"
    },
    onKeyDown: e => {
      if (e.key === "Enter") {
        const val = e.target.value.trim();
        if (val) {
          localStorage.setItem("tdr_api_token", val);
          reloadData();
        }
      }
    }
  }), /*#__PURE__*/React.createElement("button", {
    className: "btn bp",
    style: {
      padding: "10px 14px",
      borderRadius: 8,
      fontWeight: 600
    },
    onClick: () => {
      const val = document.getElementById("tokenInput").value.trim();
      if (val) {
        localStorage.setItem("tdr_api_token", val);
        reloadData();
      }
    }
  }, "Verify & Unlock"))));
  if (apiError) return /*#__PURE__*/React.createElement("div", {
    style: {
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
      background: "var(--bg0)"
    }
  }, /*#__PURE__*/React.createElement("header", {
    className: "hdr"
  }, /*#__PURE__*/React.createElement("div", {
    className: "logo",
    style: {
      background: "rgba(239,68,68,.2)",
      color: C.red
    }
  }, "!"), /*#__PURE__*/React.createElement("div", {
    className: "hdr-t"
  }, /*#__PURE__*/React.createElement("h2", null, "Dashboard Error"), /*#__PURE__*/React.createElement("p", null, "Cannot connect to Flask API"))), /*#__PURE__*/React.createElement("div", {
    className: "ld-wrap"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: C.red,
      fontWeight: 600
    }
  }, "⚠ ", apiError), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--t3)",
      marginTop: 4
    }
  }, "Make sure ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--mono)",
      color: C.cyan
    }
  }, "dashboard_api.py"), " is running on port 8503"), /*#__PURE__*/React.createElement("button", {
    className: "btn bp",
    style: {
      marginTop: 12
    },
    onClick: reloadData
  }, "↺ Retry")));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: "100%",
      height: "100vh",
      display: "flex",
      overflow: "hidden",
      position: "relative"
    }
  }, !isMobile && /*#__PURE__*/React.createElement("div", {
    className: `sb${col ? " col" : ""}`
  }, /*#__PURE__*/React.createElement("div", {
    className: "sb-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "logo",
    style: {
      background: "white",
      padding: "2px"
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "assets/csg-logo.jpg",
    alt: "CSG",
    style: {
      width: "100%",
      height: "100%",
      objectFit: "contain",
      display: "block",
      borderRadius: "4px"
    },
    onError: e => {
      e.target.style.display = 'none';
      e.target.parentElement.style.background = 'linear-gradient(135deg, #3B82F6, #0EA5E9)';
      e.target.parentElement.style.padding = '0';
      e.target.parentElement.innerHTML = 'TDR';
    }
  })), !col && /*#__PURE__*/React.createElement("div", {
    className: "sb-brand"
  }, /*#__PURE__*/React.createElement("h1", null, "TIEN-TAN THUAN PORT"), /*#__PURE__*/React.createElement("p", null, "TDR Processor ", metaVer))), /*#__PURE__*/React.createElement("div", {
    className: "sb-nav"
  }, /*#__PURE__*/React.createElement("div", {
    className: "nav-sec"
  }, col ? "" : "MAIN"), NAV.map(n => /*#__PURE__*/React.createElement("div", {
    key: n.id,
    className: `nav-i${nav === n.id ? " act" : ""}`,
    onClick: () => setNav(n.id)
  }, /*#__PURE__*/React.createElement("span", {
    className: "ni"
  }, n.icon), !col && /*#__PURE__*/React.createElement("span", {
    className: "nl"
  }, n.lbl), !col && n.id === "delays" && delays.length > 0 && /*#__PURE__*/React.createElement("span", {
    className: "nb"
  }, delays.length))), !col && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "nav-sec"
  }, "DATA"), /*#__PURE__*/React.createElement("div", {
    className: "nav-i"
  }, /*#__PURE__*/React.createElement("span", {
    className: "ni"
  }, "🗄"), /*#__PURE__*/React.createElement("span", {
    className: "nl"
  }, "SQLite · ", dbStatus === "healthy" ? "Connected" : "CSV Fallback")), /*#__PURE__*/React.createElement("div", {
    className: "nav-i"
  }, /*#__PURE__*/React.createElement("span", {
    className: "ni"
  }, "📂"), /*#__PURE__*/React.createElement("span", {
    className: "nl"
  }, vessels.length, " vessels · ", qcData.length, " QC")))), !col && /*#__PURE__*/React.createElement("div", {
    className: "sb-filt"
  }, /*#__PURE__*/React.createElement("div", {
    className: "sb-filt-title",
    onClick: () => setFiltOpen(o => !o)
  }, /*#__PURE__*/React.createElement("span", null, "🔍 FILTERS", activeFiltersCount > 0 ? ` (${activeFiltersCount})` : ""), activeFiltersCount > 0 && /*#__PURE__*/React.createElement("button", {
    className: "sb-filt-clr",
    onClick: e => {
      e.stopPropagation();
      setFDateFrom("");
      setFDateTo("");
      setFOp("");
      setFBerth("");
      setFVessel("");
    }
  }, "✕ Clear")), filtOpen && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "sb-filt-field",
    style: {
      marginBottom: 8
    }
  }, /*#__PURE__*/React.createElement("label", {
    className: "sb-filt-lbl",
    style: {
      display: 'block',
      marginBottom: 4
    }
  }, "📅 Date Range (ATB)"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9,
      color: 'var(--t4)',
      width: 28,
      fontWeight: 600
    }
  }, "From"), /*#__PURE__*/React.createElement("input", {
    type: "date",
    className: "sb-filt-inp",
    value: fDateFrom,
    min: dateMin,
    max: fDateTo || dateMax,
    onChange: e => setFDateFrom(e.target.value),
    onClick: e => e.target.showPicker?.(),
    style: {
      flex: 1,
      cursor: 'pointer',
      fontSize: 10.5,
      padding: '3px 6px',
      background: 'var(--bg3)',
      border: '1px solid var(--br2)',
      color: 'var(--t2)',
      borderRadius: 4,
      outline: 'none',
      height: 24,
      boxSizing: 'border-box'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9,
      color: 'var(--t4)',
      width: 28,
      fontWeight: 600
    }
  }, "To"), /*#__PURE__*/React.createElement("input", {
    type: "date",
    className: "sb-filt-inp",
    value: fDateTo,
    min: fDateFrom || dateMin,
    max: dateMax,
    onChange: e => setFDateTo(e.target.value),
    onClick: e => e.target.showPicker?.(),
    style: {
      flex: 1,
      cursor: 'pointer',
      fontSize: 10.5,
      padding: '3px 6px',
      background: 'var(--bg3)',
      border: '1px solid var(--br2)',
      color: 'var(--t2)',
      borderRadius: 4,
      outline: 'none',
      height: 24,
      boxSizing: 'border-box'
    }
  })))), /*#__PURE__*/React.createElement("div", {
    className: "sb-filt-field"
  }, /*#__PURE__*/React.createElement("label", {
    className: "sb-filt-lbl"
  }, "🏢 Operator (Hãng tàu)"), /*#__PURE__*/React.createElement("select", {
    className: "sb-filt-inp",
    value: fOp,
    onChange: e => setFOp(e.target.value)
  }, /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "All Operators"), allOps.map(o => /*#__PURE__*/React.createElement("option", {
    key: o,
    value: o
  }, o)))), /*#__PURE__*/React.createElement("div", {
    className: "sb-filt-field"
  }, /*#__PURE__*/React.createElement("label", {
    className: "sb-filt-lbl"
  }, "⚓ Berth (Cầu bến)"), /*#__PURE__*/React.createElement("select", {
    className: "sb-filt-inp",
    value: fBerth,
    onChange: e => setFBerth(e.target.value)
  }, /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "All Berths"), allBerths.map(b => /*#__PURE__*/React.createElement("option", {
    key: b,
    value: b
  }, b)))), /*#__PURE__*/React.createElement("div", {
    className: "sb-filt-field"
  }, /*#__PURE__*/React.createElement("label", {
    className: "sb-filt-lbl"
  }, "🚢 Vessel (Tàu)"), /*#__PURE__*/React.createElement("select", {
    className: "sb-filt-inp",
    value: fVessel,
    onChange: e => setFVessel(e.target.value)
  }, /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "All Vessels"), allVessels.map(v => /*#__PURE__*/React.createElement("option", {
    key: v,
    value: v
  }, v)))))), /*#__PURE__*/React.createElement("div", {
    className: "sb-foot"
  }, !col && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9.5,
      color: "var(--t4)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "pulse"
  }), "API ", dbStatus, " · ", reportDate || "—"))), /*#__PURE__*/React.createElement("div", {
    className: "main"
  }, /*#__PURE__*/React.createElement("header", {
    className: "hdr"
  }, !isMobile && /*#__PURE__*/React.createElement("button", {
    className: "hdr-tog",
    onClick: () => setCol(c => !c)
  }, col ? "→" : "←"), /*#__PURE__*/React.createElement("div", {
    className: "hdr-t"
  }, /*#__PURE__*/React.createElement("h2", null, PT[nav]), /*#__PURE__*/React.createElement("p", null, getHeaderSubtitle(), activeFiltersCount > 0 ? ` · 🔍 ${activeFiltersCount} filter${activeFiltersCount > 1 ? "s" : ""} active` : "")), !isMobile && /*#__PURE__*/React.createElement("div", {
    className: "hdr-filt",
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6,
      background: "var(--bg3)",
      border: "1px solid var(--br2)",
      borderRadius: 6,
      padding: "2px 8px",
      cursor: "default"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11
    }
  }, "🎯 Target KPI:"), /*#__PURE__*/React.createElement("input", {
    type: "number",
    value: kt,
    onChange: e => {
      const v = parseInt(e.target.value, 10);
      if (!isNaN(v) && v > 0) setCustomKt(v);
    },
    style: {
      width: 42,
      background: "var(--bg0)",
      border: "1px solid var(--br2)",
      color: "var(--t1)",
      fontSize: 11.5,
      textAlign: "center",
      borderRadius: 4,
      padding: "2px 0",
      outline: "none",
      fontWeight: 700,
      fontFamily: "inherit"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9.5,
      color: "var(--t4)"
    }
  }, "M/h")), !isMobile && /*#__PURE__*/React.createElement("div", {
    className: "hdr-tab-actions",
    style: {
      display: "flex",
      gap: 6,
      alignItems: "center"
    }
  }, nav === "overview" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    onClick: () => exportToCSV(vessels, "vessel_summary")
  }, "↓ Export"), /*#__PURE__*/React.createElement("button", {
    className: "btn bp",
    onClick: reloadData
  }, "⚡ Refresh")), nav === "vessels" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    onClick: () => exportToCSV(vessels, "vessel_summary")
  }, "↓ Export"), /*#__PURE__*/React.createElement("button", {
    className: "btn br2x"
  }, "⚠ ", vessels.filter(v => (v.nmph || 0) < kt).length, " Below KPI")), nav === "cranes" && /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    onClick: () => exportToCSV(filteredQc, "qc_productivity")
  }, "↓ Export"), nav === "operators" && /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    onClick: () => exportToCSV(filteredQcOp, "qc_operator_productivity")
  }, "↓ Export"), nav === "delays" && /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    onClick: () => exportToCSV(delays, "delay_details")
  }, "↓ Export"), nav === "config" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    onClick: () => exportToCSV(vessels, "system_logs")
  }, "↓ Export Logs"), /*#__PURE__*/React.createElement("button", {
    className: "btn bp"
  }, "⚡ Process TDR Files"))), /*#__PURE__*/React.createElement("div", {
    className: "hdr-act",
    style: {
      position: "relative",
      display: "flex",
      gap: "6px",
      alignItems: "center"
    }
  }, !isMobile && /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative"
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ic-btn",
    onClick: () => setNotif(o => !o)
  }, "🔔", NOTIFS.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "nd"
  })), notif && /*#__PURE__*/React.createElement("div", {
    className: "np"
  }, /*#__PURE__*/React.createElement("div", {
    className: "np-hd"
  }, "Alerts (", NOTIFS.length, ")", /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: "var(--t4)",
      cursor: "pointer"
    },
    onClick: () => setNotif(false)
  }, "✕")), NOTIFS.length ? NOTIFS.map((n, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "np-i"
  }, /*#__PURE__*/React.createElement("div", {
    className: "np-t",
    style: {
      borderLeft: `2px solid ${n.c}`,
      paddingLeft: 6
    }
  }, n.t), /*#__PURE__*/React.createElement("div", {
    className: "np-s"
  }, n.s))) : /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "14px 12px",
      color: "var(--t4)",
      fontSize: 11
    }
  }, "No alerts — all vessels meeting KPI"))), /*#__PURE__*/React.createElement("button", {
    className: "ic-btn",
    onClick: () => setTheme(t => t === "dark" ? "light" : "dark"),
    title: theme === "dark" ? "Switch to Light Theme" : "Switch to Dark Theme",
    style: {
      fontFamily: "inherit",
      outline: "none"
    }
  }, theme === "dark" ? "☀️" : "🌙"), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ava",
    onClick: () => setUprof(o => !o),
    style: {
      cursor: 'pointer'
    }
  }, userInitials), uprof && /*#__PURE__*/React.createElement("div", {
    className: "np",
    style: {
      right: 0,
      width: 220
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "np-hd",
    style: {
      padding: '16px 20px',
      borderBottom: '1px solid var(--br)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ava",
    style: {
      width: 32,
      height: 32,
      fontSize: 12
    }
  }, userInitials), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 700,
      color: 'var(--t1)'
    }
  }, userName), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--t4)'
    }
  }, userRole)))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '8px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "np-i",
    style: {
      padding: '10px 20px',
      cursor: 'pointer'
    },
    onClick: () => {
      setShowSettings(true);
      setUprof(false);
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "np-t"
  }, "Account Settings")), /*#__PURE__*/React.createElement("div", {
    className: "np-i",
    style: {
      padding: '10px 20px',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "np-t"
  }, "Simulation Control")), /*#__PURE__*/React.createElement("div", {
    className: "np-i",
    style: {
      padding: '10px 20px',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "np-t"
  }, "Help & Support")), /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '8px 20px',
      height: 1,
      background: 'var(--br)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "np-i",
    style: {
      padding: '10px 20px',
      cursor: 'pointer',
      color: 'var(--red)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "np-t"
  }, "Sign Out"))))))), showSettings && /*#__PURE__*/React.createElement("div", {
    className: "modal-overlay",
    style: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.5)',
      zIndex: 999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backdropFilter: 'blur(2px)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      width: 400,
      padding: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, "Account Settings"), /*#__PURE__*/React.createElement("div", {
    className: "tab",
    onClick: () => setShowSettings(false)
  }, "✕")), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      padding: 24,
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "gcol",
    style: {
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("label", {
    style: {
      fontSize: 11,
      fontWeight: 600,
      color: 'var(--t4)'
    }
  }, "DISPLAY NAME"), /*#__PURE__*/React.createElement("input", {
    className: "input",
    style: {
      width: '100%',
      padding: '10px 12px',
      borderRadius: 6,
      border: '1px solid var(--br)',
      background: 'var(--bg2)',
      color: 'var(--t1)',
      outline: 'none'
    },
    value: userName,
    onChange: e => setUserName(e.target.value),
    placeholder: "Enter your name"
  })), /*#__PURE__*/React.createElement("div", {
    className: "gcol",
    style: {
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("label", {
    style: {
      fontSize: 11,
      fontWeight: 600,
      color: 'var(--t4)'
    }
  }, "SYSTEM ROLE"), /*#__PURE__*/React.createElement("input", {
    className: "input",
    style: {
      width: '100%',
      padding: '10px 12px',
      borderRadius: 6,
      border: '1px solid var(--br)',
      background: 'var(--bg2)',
      color: 'var(--t1)',
      outline: 'none'
    },
    value: userRole,
    onChange: e => setUserRole(e.target.value),
    placeholder: "e.g. Terminal Manager"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'flex-end',
      marginTop: 8
    }
  }, /*#__PURE__*/React.createElement("button", {
    className: "btn bp",
    style: {
      padding: '8px 20px'
    },
    onClick: () => setShowSettings(false)
  }, "Save Changes"))))), isMobile ? /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflowY: "auto"
    }
  }, /*#__PURE__*/React.createElement(MobilePages, {
    nav: nav,
    kpi: kpi,
    vessels: vessels,
    qcData: qcData,
    qcTimeline: qcTimeline,
    berthStatus: berthStatus,
    delays: delays,
    qcOpData: qcOpData,
    kt: kt,
    theme: theme
  })) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("main", {
    className: "cnt"
  }, nav === "overview" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "kg k6"
  }, /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Active Vessels",
    val: kpi.tvs,
    ic: C.blue,
    icon: "⛵",
    dl: `${kpi.above} above KPI`,
    dlt: "pos",
    spark: sp.v
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Total TEUs",
    val: kpi.tteus.toLocaleString(),
    ic: C.purple,
    icon: "📦",
    dl: "all vessels",
    dlt: "pos",
    spark: sp.t
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Avg Net M/h",
    val: kpi.avgNmph.toFixed(1),
    ic: moveDelta >= 0 ? C.green : C.red,
    icon: "📈",
    dl: `${moveDelta >= 0 ? "+" : ""}${moveDelta.toFixed(1)} vs KPI`,
    dlt: moveDelta >= 0 ? "pos" : "neg",
    spark: sp.nm
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Avg Portstay",
    val: kpi.avgPs.toFixed(1),
    unit: "h",
    ic: C.cyan,
    icon: "⚓",
    dl: "per vessel",
    dlt: "neu",
    spark: sp.ps
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Total Delay Hrs",
    val: kpi.tdHrs.toFixed(1),
    unit: "h",
    ic: C.amber,
    icon: "⏱",
    dl: `${delays.length} events`,
    dlt: "neg",
    spark: sp.dh
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Terminal Conv. %",
    val: `${kpi.tcPct}%`,
    ic: C.red,
    icon: "⚠",
    dl: "of total delay",
    dlt: "neg",
    spark: sp.de
  })), /*#__PURE__*/React.createElement("div", {
    className: "g23"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.purple
    }
  }), "Operator Performance"), /*#__PURE__*/React.createElement("div", {
    className: "tabs"
  }, ["MTD", "QTD", "YTD"].map(t => /*#__PURE__*/React.createElement("div", {
    key: t,
    className: `tab${opTab === t ? " ac" : ""}`,
    onClick: () => setOpTab(t)
  }, t)))), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      height: 180
    }
  }, /*#__PURE__*/React.createElement(OpBarChart, {
    data: operators,
    kt: kt,
    theme: theme
  }))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.cyan
    }
  }), "Live Berth Status"), /*#__PURE__*/React.createElement("span", {
    className: "bx bc_"
  }, berthStatus.filter(b => b.vessel).length, " Occupied")), /*#__PURE__*/React.createElement("div", {
    className: "cb"
  }, /*#__PURE__*/React.createElement(BerthMap, {
    berths: berthStatus
  })))), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.blue
    }
  }), "Vessel Operations — Dense View"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9.5,
      color: "var(--t3)"
    }
  }, vessels.length, " vessels")), /*#__PURE__*/React.createElement(VesselTable, {
    data: vessels,
    perPage: 8
  }))), nav === "vessels" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "kg k6"
  }, /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Total Vessels",
    val: vessels.length,
    ic: C.blue,
    icon: "⛵",
    dl: "all records",
    dlt: "pos",
    spark: sp.v
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Total TEUs",
    val: kpi.tteus.toLocaleString(),
    ic: C.purple,
    icon: "📦",
    dl: "total",
    dlt: "pos",
    spark: sp.t
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Avg Portstay",
    val: kpi.avgPs.toFixed(1),
    unit: "h",
    ic: C.cyan,
    icon: "⚓",
    dl: "average",
    dlt: "neu",
    spark: sp.ps
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Avg Net Wk",
    val: kpi.avgNet.toFixed(1),
    unit: "h",
    ic: C.amber,
    icon: "⏱",
    dl: "average",
    dlt: "neu",
    spark: sp.nw
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Avg Net M/h",
    val: kpi.avgNmph.toFixed(1),
    ic: moveDelta >= 0 ? C.green : C.red,
    icon: "📈",
    dl: `${moveDelta >= 0 ? "+" : ""}${moveDelta.toFixed(1)} KPI`,
    dlt: moveDelta >= 0 ? "pos" : "neg",
    spark: sp.nm
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Above KPI",
    val: `${kpi.above}/${kpi.tvs}`,
    ic: C.green,
    icon: "✓",
    dl: "passing",
    dlt: "pos",
    spark: sp.v
  })), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.blue
    }
  }), "All Vessel Records"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9.5,
      color: "var(--t3)"
    }
  }, vessels.length, " records")), /*#__PURE__*/React.createElement(VesselTable, {
    data: vessels,
    perPage: 20
  }))), nav === "market" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "kg k3",
    style: {
      marginBottom: 20
    }
  }, /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Total Market Moves",
    val: Object.values(marketStats.cargo).reduce((a, b) => a + b, 0).toLocaleString(),
    ic: C.blue,
    icon: "📦",
    dl: "Total volume",
    dlt: "pos",
    spark: sp.t
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Import Ratio (Discharge)",
    val: `${Math.round((marketStats.cargo.Discharge || 0) / (Object.values(marketStats.cargo).reduce((a, b) => a + b, 0) || 1) * 100)}%`,
    ic: C.cyan,
    icon: "📉",
    dl: "Market share",
    dlt: "pos",
    spark: sp.t
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Export Ratio (Load)",
    val: `${Math.round((marketStats.cargo.Load || 0 || marketStats.cargo.Loading) / (Object.values(marketStats.cargo).reduce((a, b) => a + b, 0) || 1) * 100)}%`,
    ic: C.green,
    icon: "📈",
    dl: "Market share",
    dlt: "pos",
    spark: sp.t
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1.2fr 1fr",
      gap: 20,
      marginBottom: 20
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      display: "flex",
      flexDirection: "column"
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.blue
    }
  }), "Cargo Mix Dist.")), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      flex: 1,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      minHeight: 200
    }
  }, /*#__PURE__*/React.createElement(DonutChart, {
    data: marketStats.cargo,
    theme: theme,
    customColors: {
      "Discharge": C.blue,
      "Loading": C.green,
      "Load": C.green,
      "Shifting": C.purple
    },
    label: "Moves"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.blue
    }
  }), "Market Volume Trends"), /*#__PURE__*/React.createElement("div", {
    className: "tabs"
  }, /*#__PURE__*/React.createElement("div", {
    className: `tab ${trendMode === 'Weekly' ? 'ac' : ''}`,
    onClick: () => setTrendMode('Weekly')
  }, "Weekly"), /*#__PURE__*/React.createElement("div", {
    className: `tab ${trendMode === 'Monthly' ? 'ac' : ''}`,
    onClick: () => setTrendMode('Monthly')
  }, "Monthly"))), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      height: 260
    }
  }, /*#__PURE__*/React.createElement(MarketTrendChart, {
    data: trendMode === 'Weekly' ? marketStats.trends : marketStats.trendsMonthly || marketStats.trends,
    theme: theme
  }))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.green
    }
  }), "Carrier Volume Share")), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      height: 260
    }
  }, /*#__PURE__*/React.createElement(MarketBarChart, {
    data: marketStats.byOp.slice(0, 8),
    theme: theme
  })))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.blue
    }
  }), "Operational Performance by Carrier (Summary)"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9.5,
      color: "var(--t3)"
    }
  }, marketStats.byOp.length, " carriers active")), /*#__PURE__*/React.createElement("div", {
    className: "tw"
  }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "Shipping Line / Operator"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "Total Moves"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "Discharge"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "Load"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "Full"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "Empty"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "Imp/Exp %"))), /*#__PURE__*/React.createElement("tbody", null, marketStats.byOp.map((o, i) => /*#__PURE__*/React.createElement("tr", {
    key: i
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      fontWeight: 600
    }
  }, o.op), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right"
    }
  }, o.total.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right",
      color: C.blue
    }
  }, o.dis.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right",
      color: C.green
    }
  }, o.load.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right",
      fontWeight: 500
    }
  }, o.full.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right",
      color: "var(--t3)"
    }
  }, o.empty.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      display: "flex",
      gap: 4,
      justifyContent: "flex-end"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: C.blue
    }
  }, Math.round(o.dis / o.total * 100), "%"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--br)"
    }
  }, "/"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: C.green
    }
  }, Math.round(o.load / o.total * 100), "%")))))))))), nav === "containers" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "kg k3",
    style: {
      marginBottom: 20
    }
  }, /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "Full Container Ratio",
    val: `${Math.round(marketStats.status.Full / (marketStats.status.Full + marketStats.status.Empty || 1) * 100)}%`,
    ic: C.blue,
    icon: "⚡",
    dl: "Laden units",
    dlt: "pos",
    spark: sp.t
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "20' (Small) Ratio",
    val: `${Math.round(marketStats.size["20'"] / (Object.values(marketStats.size).reduce((a, b) => a + b, 0) || 1) * 100)}%`,
    ic: C.cyan,
    icon: "📏",
    dl: "Standard short",
    dlt: "neu",
    spark: sp.t
  }), /*#__PURE__*/React.createElement(KpiCard, {
    lbl: "40/45' (Large) Ratio",
    val: `${Math.round((marketStats.size["40'"] + marketStats.size["45'"]) / (Object.values(marketStats.size).reduce((a, b) => a + b, 0) || 1) * 100)}%`,
    ic: C.teal,
    icon: "📐",
    dl: "Standard long",
    dlt: "pos",
    spark: sp.t
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1.2fr 1fr",
      gap: 20,
      marginBottom: 20
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      display: "flex",
      flexDirection: "column"
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.blue
    }
  }), "Status Mix (Full/Empty)")), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      flex: 1,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      minHeight: 220
    }
  }, /*#__PURE__*/React.createElement(DonutChart, {
    data: marketStats.status,
    theme: theme,
    customColors: {
      "Full": C.blue,
      "Empty": "#3D556E"
    },
    label: "Total"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.cyan
    }
  }), "Carrier Status Distribution")), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      height: 260
    }
  }, /*#__PURE__*/React.createElement(ContainerBarChart, {
    data: marketStats.byOp.map(o => ({
      ...o,
      full: o.full,
      empty: o.empty
    })).slice(0, 8),
    theme: theme
  }))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.teal
    }
  }), "Carrier Size Mix Distribution")), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      height: 260
    }
  }, /*#__PURE__*/React.createElement(SizeMixBarChart, {
    data: marketStats.byOp.map(o => ({
      op: o.op,
      s20: o.s20,
      s40: o.s40,
      s45: o.s45
    })).slice(0, 8),
    theme: theme
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1.8fr 1fr",
      gap: 20,
      marginBottom: 20
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.blue
    }
  }), "Container Inventory Breakdown by Carrier"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9.5,
      color: "var(--t3)"
    }
  }, marketStats.byOp.length, " carriers active")), /*#__PURE__*/React.createElement("div", {
    className: "tw"
  }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "Shipping Line / Operator"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "Total Moves"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "Full (Laden)"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "Empty"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "20' (Short)"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: "right"
    }
  }, "40/45' (Long)"))), /*#__PURE__*/React.createElement("tbody", null, marketStats.byOp.map((o, i) => /*#__PURE__*/React.createElement("tr", {
    key: i
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      fontWeight: 600
    }
  }, o.op), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right"
    }
  }, o.total.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right",
      color: C.blue,
      fontWeight: 500
    }
  }, o.full.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right",
      color: "var(--t3)"
    }
  }, o.empty.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right",
      color: C.cyan
    }
  }, o.s20.toLocaleString()), /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: "right",
      color: C.teal
    }
  }, (o.s40 + o.s45).toLocaleString()))))))), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      display: "flex",
      flexDirection: "column"
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.cyan
    }
  }), "Global Size Distribution")), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      flex: 1,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      minHeight: 220
    }
  }, /*#__PURE__*/React.createElement(DonutChart, {
    data: marketStats.size,
    theme: theme,
    customColors: {
      "20'": C.cyan,
      "40'": C.teal,
      "45'": C.blue
    },
    label: "Size"
  }))))), nav === "cranes" && (() => {
    const craneIds = ["ALL", ...Array.from(new Set(qcData.map(q => q.qc))).sort()];
    const qcPerPage = 12;
    const sortedQc = [...filteredQc].sort((a, b) => a.qc.localeCompare(b.qc) || (a.vessel || '').localeCompare(b.vessel || ''));
    const activeQcPageRows = sortedQc.slice(qcPg * qcPerPage, (qcPg + 1) * qcPerPage);
    const totalPages = Math.ceil(filteredQc.length / qcPerPage);
    const avgGmh = filteredQc.length ? filteredQc.reduce((s, q) => s + q.gmh, 0) / filteredQc.length : 0;
    const avgNmh = filteredQc.length ? filteredQc.reduce((s, q) => s + q.nmh, 0) / filteredQc.length : 0;
    const totalDelayH = filteredQc.reduce((s, q) => s + q.dH, 0);
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      className: "kg k4"
    }, /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Active Cranes",
      val: qcTimeline.length,
      ic: C.blue,
      icon: "⚙",
      dl: "assigned",
      dlt: "neu",
      spark: sp.v
    }), /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Avg Gross M/h",
      val: avgGmh.toFixed(1),
      ic: C.blue,
      icon: "📊",
      dl: "gross productivity",
      dlt: "neu",
      spark: sp.nm
    }), /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Avg Net M/h",
      val: avgNmh.toFixed(1),
      ic: C.green,
      icon: "📈",
      dl: "net productivity",
      dlt: "pos",
      spark: sp.nm
    }), /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Total Delay",
      val: totalDelayH.toFixed(1),
      unit: "h",
      ic: C.amber,
      icon: "⏱",
      dl: "delay hours",
      dlt: "neg",
      spark: sp.dl
    })), /*#__PURE__*/React.createElement("div", {
      className: "card",
      style: {
        marginBottom: 8
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "ch"
    }, /*#__PURE__*/React.createElement("div", {
      className: "ct"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cdot",
      style: {
        background: C.blue
      }
    }), "Crane Activity & Allocation Summary"), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 9.5,
        color: "var(--t3)"
      }
    }, qcTimeline.length, " active cranes")), /*#__PURE__*/React.createElement("div", {
      className: "tw"
    }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "QC Crane"), /*#__PURE__*/React.createElement("th", null, "Assigned Vessels"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Vessels Count"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Gross Hours"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Net Hours"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Delay Hours"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Total Moves"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Avg Gross M/h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Avg Net M/h"))), /*#__PURE__*/React.createElement("tbody", null, (() => {
      const m = {};
      qcData.forEach(q => {
        if (!m[q.qc]) m[q.qc] = {
          qc: q.qc,
          vessels: new Set(),
          gH: 0,
          nH: 0,
          dH: 0,
          tot: 0
        };
        const r = m[q.qc];
        r.vessels.add(q.vessel);
        r.gH += q.gH;
        r.nH += q.nH;
        r.dH += q.dH;
        r.tot += q.tot;
      });
      const summary = Object.values(m).map(r => ({
        ...r,
        vesselList: Array.from(r.vessels).join(", "),
        vesselsCount: r.vessels.size,
        gmh: r.gH > 0 ? r.tot / r.gH : 0,
        nmh: r.nH > 0 ? r.tot / r.nH : 0
      })).sort((a, b) => a.qc.localeCompare(b.qc));
      return summary.map((r, i) => /*#__PURE__*/React.createElement("tr", {
        key: i
      }, /*#__PURE__*/React.createElement("td", {
        className: "tb"
      }, /*#__PURE__*/React.createElement("span", {
        className: "bx bc_",
        style: {
          fontFamily: "var(--mono)"
        }
      }, r.qc)), /*#__PURE__*/React.createElement("td", {
        style: {
          maxWidth: 240,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          color: 'var(--t3)'
        },
        title: r.vesselList
      }, r.vesselList), /*#__PURE__*/React.createElement("td", {
        className: "tr"
      }, r.vesselsCount), /*#__PURE__*/React.createElement("td", {
        className: "tr"
      }, r.gH.toFixed(1), "h"), /*#__PURE__*/React.createElement("td", {
        className: "tr"
      }, r.nH.toFixed(1), "h"), /*#__PURE__*/React.createElement("td", {
        className: "tr",
        style: {
          color: r.dH > 10 ? C.amber : 'inherit'
        }
      }, r.dH.toFixed(1), "h"), /*#__PURE__*/React.createElement("td", {
        className: "tr tb"
      }, r.tot.toLocaleString()), /*#__PURE__*/React.createElement("td", {
        className: "tr"
      }, r.gmh.toFixed(1)), /*#__PURE__*/React.createElement("td", {
        className: "tr",
        style: {
          fontWeight: 700,
          color: C.green
        }
      }, r.nmh.toFixed(1))));
    })())))), /*#__PURE__*/React.createElement("div", {
      className: "g2",
      style: {
        flex: 1
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "card",
      style: {
        flex: 1
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "ch"
    }, /*#__PURE__*/React.createElement("div", {
      className: "ct"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cdot",
      style: {
        background: C.green
      }
    }), "Gross vs Net M/h — by ", craneGroupBy === 'day' ? 'Day' : craneGroupBy === 'week' ? 'Week' : craneGroupBy === 'month' ? 'Month' : 'Quarter'), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 4
      }
    }, /*#__PURE__*/React.createElement("select", {
      value: selectedCrane,
      onChange: e => {
        setSelectedCrane(e.target.value);
        setQcPg(0);
      },
      style: {
        background: 'var(--bg3)',
        border: '1px solid var(--br2)',
        color: 'var(--t2)',
        fontSize: 10,
        borderRadius: 4,
        padding: '2px 6px',
        outline: 'none',
        fontFamily: 'inherit',
        cursor: 'pointer'
      }
    }, craneIds.map(c => /*#__PURE__*/React.createElement("option", {
      key: c,
      value: c
    }, c === 'ALL' ? 'All Cranes' : c))), /*#__PURE__*/React.createElement("select", {
      value: craneGroupBy,
      onChange: e => setCraneGroupBy(e.target.value),
      style: {
        background: 'var(--bg3)',
        border: '1px solid var(--br2)',
        color: 'var(--t2)',
        fontSize: 10,
        borderRadius: 4,
        padding: '2px 6px',
        outline: 'none',
        fontFamily: 'inherit',
        cursor: 'pointer'
      }
    }, /*#__PURE__*/React.createElement("option", {
      value: "day"
    }, "By Day"), /*#__PURE__*/React.createElement("option", {
      value: "week"
    }, "By Week"), /*#__PURE__*/React.createElement("option", {
      value: "month"
    }, "By Month"), /*#__PURE__*/React.createElement("option", {
      value: "quarter"
    }, "By Quarter")))), /*#__PURE__*/React.createElement("div", {
      className: "cb",
      style: {
        height: 190
      }
    }, /*#__PURE__*/React.createElement(QCBarChart, {
      data: groupedChartData,
      theme: theme
    }))), /*#__PURE__*/React.createElement("div", {
      className: "card",
      style: {
        flex: 1
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "ch"
    }, /*#__PURE__*/React.createElement("div", {
      className: "ct"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cdot",
      style: {
        background: C.purple
      }
    }), "QC Detail Records"), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 9.5,
        color: "var(--t3)"
      }
    }, selectedCrane === 'ALL' ? qcData.length + ' records' : selectedCrane)), /*#__PURE__*/React.createElement("div", {
      className: "tw"
    }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "QC"), /*#__PURE__*/React.createElement("th", null, "Vessel"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Gross h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Net h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Delay h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Total"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "G M/h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "N M/h"))), /*#__PURE__*/React.createElement("tbody", null, activeQcPageRows.map((q, i) => /*#__PURE__*/React.createElement("tr", {
      key: i
    }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("span", {
      className: "bx bc_",
      style: {
        fontFamily: "var(--mono)"
      }
    }, q.qc)), /*#__PURE__*/React.createElement("td", {
      className: "tb",
      style: {
        maxWidth: 120,
        overflow: "hidden",
        textOverflow: "ellipsis"
      }
    }, q.vessel), /*#__PURE__*/React.createElement("td", {
      className: "tr"
    }, q.gH.toFixed(1)), /*#__PURE__*/React.createElement("td", {
      className: "tr"
    }, q.nH.toFixed(1)), /*#__PURE__*/React.createElement("td", {
      className: "tr",
      style: {
        color: C.amber
      }
    }, q.dH.toFixed(1)), /*#__PURE__*/React.createElement("td", {
      className: "tr tb"
    }, q.tot), /*#__PURE__*/React.createElement("td", {
      className: "tr"
    }, q.gmh.toFixed(1)), /*#__PURE__*/React.createElement("td", {
      className: "tr",
      style: {
        fontWeight: 600
      }
    }, q.nmh.toFixed(1))))))), totalPages > 1 && /*#__PURE__*/React.createElement("div", {
      className: "pgr"
    }, /*#__PURE__*/React.createElement("span", {
      className: "pgi"
    }, qcPg * qcPerPage + 1, "–", Math.min((qcPg + 1) * qcPerPage, filteredQc.length), " of ", filteredQc.length), /*#__PURE__*/React.createElement("button", {
      className: "pb",
      onClick: () => setQcPg(p => p - 1),
      disabled: qcPg === 0
    }, "‹"), renderPageButtons(qcPg, totalPages, setQcPg), /*#__PURE__*/React.createElement("button", {
      className: "pb",
      onClick: () => setQcPg(p => p + 1),
      disabled: qcPg >= totalPages - 1
    }, "›")))));
  })(), nav === "operators" && (() => {
    const craneIds = ["ALL", ...Array.from(new Set(qcOpData.map(q => q.qc))).sort()];
    const qcPerPage = 12;
    const sortedQc = [...filteredQcOp].sort((a, b) => a.qc.localeCompare(b.qc) || (a.vessel || '').localeCompare(b.vessel || ''));
    const activeQcPageRows = sortedQc.slice(qcPg * qcPerPage, (qcPg + 1) * qcPerPage);
    const totalPages = Math.ceil(filteredQcOp.length / qcPerPage);
    const avgGmh = filteredQcOp.length ? filteredQcOp.reduce((s, q) => s + q.gmh, 0) / filteredQcOp.length : 0;
    const avgNmh = filteredQcOp.length ? filteredQcOp.reduce((s, q) => s + q.nmh, 0) / filteredQcOp.length : 0;
    const totalDelayH = filteredQcOp.reduce((s, q) => s + q.dH, 0);
    const activeCranesCount = new Set(filteredQcOp.map(q => q.qc)).size;
    const avgGmhCrane = qcData.length ? qcData.reduce((s, q) => s + q.gmh, 0) / qcData.length : 0;
    const avgNmhCrane = qcData.length ? qcData.reduce((s, q) => s + q.nmh, 0) / qcData.length : 0;
    const gmhDelta = avgGmh - avgGmhCrane;
    const nmhDelta = avgNmh - avgNmhCrane;
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      style: {
        background: "linear-gradient(135deg,rgba(245,158,11,.12),rgba(6,182,212,.08))",
        border: "1px solid rgba(245,158,11,.3)",
        borderRadius: 8,
        padding: "10px 14px",
        marginBottom: 8,
        display: "flex",
        gap: 12,
        alignItems: "flex-start"
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 18,
        lineHeight: 1,
        flexShrink: 0
      }
    }, "💡"), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        lineHeight: 1.65,
        color: "var(--t2)"
      }
    }, /*#__PURE__*/React.createElement("strong", {
      style: {
        color: C.amber
      }
    }, "Điều chỉnh theo Operator"), " — Tab này chỉ tính thời gian dừng do ", /*#__PURE__*/React.createElement("strong", null, "người lái cần trục"), " kiểm soát (Stop Time). Các nguyên nhân ngoài tầm kiểm soát (sự cố thiết bị, chờ tàu, thời tiết…) ", /*#__PURE__*/React.createElement("strong", null, "đã được loại trừ"), ".", (nmhDelta > 0 || gmhDelta > 0) && /*#__PURE__*/React.createElement("span", {
      style: {
        color: C.green
      }
    }, " ▲ Net M/h cao hơn Crane tab ", nmhDelta >= 0 ? "+" : "", nmhDelta.toFixed(1), " M/h."), nmhDelta <= 0 && gmhDelta <= 0 && nmhDelta !== 0 && /*#__PURE__*/React.createElement("span", {
      style: {
        color: C.amber
      }
    }, " Net M/h thấp hơn Crane tab ", nmhDelta.toFixed(1), " M/h — kiểm tra dữ liệu Stop Time."))), /*#__PURE__*/React.createElement("div", {
      className: "kg k4"
    }, /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Active Cranes",
      val: activeCranesCount,
      ic: C.cyan,
      icon: "⚙",
      dl: "cần trục hoạt động",
      dlt: "neu",
      spark: sp.v
    }), /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Avg Gross M/h ★",
      val: avgGmh.toFixed(1),
      ic: C.amber,
      icon: "📊",
      dl: `${gmhDelta >= 0 ? "+" : ""}${gmhDelta.toFixed(1)} vs Crane tab`,
      dlt: gmhDelta >= 0 ? "pos" : "neg",
      spark: sp.nm
    }), /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Avg Net M/h ★",
      val: avgNmh.toFixed(1),
      ic: C.green,
      icon: "📈",
      dl: `${nmhDelta >= 0 ? "+" : ""}${nmhDelta.toFixed(1)} vs Crane tab`,
      dlt: nmhDelta >= 0 ? "pos" : "neg",
      spark: sp.nm
    }), /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Total Stop Time",
      val: totalDelayH.toFixed(1),
      unit: "h",
      ic: C.amber,
      icon: "⏱",
      dl: "do Operator kiểm soát",
      dlt: "neg",
      spark: sp.dl
    })), /*#__PURE__*/React.createElement("div", {
      className: "card",
      style: {
        marginBottom: 8,
        borderColor: "rgba(245,158,11,.25)"
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "ch"
    }, /*#__PURE__*/React.createElement("div", {
      className: "ct"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cdot",
      style: {
        background: C.amber
      }
    }), "Hiệu suất theo Cần trục — Điều chỉnh Operator ", /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 9,
        color: "var(--t4)",
        marginLeft: 4
      }
    }, "(★ Net M/h = Total Conts ÷ Net Working hrs)")), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 9.5,
        color: "var(--t3)"
      }
    }, craneIds.length - 1, " cranes")), /*#__PURE__*/React.createElement("div", {
      className: "tw"
    }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "QC"), /*#__PURE__*/React.createElement("th", null, "Tàu phụ trách"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Số tàu"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Gross Wk (h)"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Net Wk (h)"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right",
        color: C.amber
      }
    }, "Stop Time (h)"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Total Conts"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Gross M/h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right",
        color: C.green
      }
    }, "Net M/h ★"))), /*#__PURE__*/React.createElement("tbody", null, (() => {
      const summaryMap = {};
      filteredQcOp.forEach(q => {
        if (!summaryMap[q.qc]) {
          summaryMap[q.qc] = {
            qc: q.qc,
            vessels: new Set(),
            gH: 0,
            nH: 0,
            dH: 0,
            tot: 0
          };
        }
        const r = summaryMap[q.qc];
        r.vessels.add(q.vessel);
        r.gH += q.gH;
        r.nH += q.nH;
        r.dH += q.dH;
        r.tot += q.tot;
      });
      const summary = Object.values(summaryMap).map(r => ({
        ...r,
        vesselsCount: r.vessels.size,
        vesselList: Array.from(r.vessels).join(", "),
        gmh: r.gH > 0 ? r.tot / r.gH : 0,
        nmh: r.nH > 0 ? r.tot / r.nH : 0
      })).sort((a, b) => b.nmh - a.nmh); // sort by best Net M/h

      return summary.map((r, i) => /*#__PURE__*/React.createElement("tr", {
        key: i
      }, /*#__PURE__*/React.createElement("td", {
        className: "tb"
      }, /*#__PURE__*/React.createElement("span", {
        className: "bx bc_",
        style: {
          fontFamily: "var(--mono)"
        }
      }, r.qc)), /*#__PURE__*/React.createElement("td", {
        style: {
          maxWidth: 240,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          color: 'var(--t3)'
        },
        title: r.vesselList
      }, r.vesselList), /*#__PURE__*/React.createElement("td", {
        className: "tr"
      }, r.vesselsCount), /*#__PURE__*/React.createElement("td", {
        className: "tr"
      }, r.gH.toFixed(1)), /*#__PURE__*/React.createElement("td", {
        className: "tr"
      }, r.nH.toFixed(1)), /*#__PURE__*/React.createElement("td", {
        className: "tr",
        style: {
          color: r.dH > 10 ? C.red : C.amber,
          fontWeight: r.dH > 10 ? 700 : 400
        }
      }, r.dH.toFixed(1)), /*#__PURE__*/React.createElement("td", {
        className: "tr tb"
      }, r.tot.toLocaleString()), /*#__PURE__*/React.createElement("td", {
        className: "tr"
      }, r.gmh.toFixed(1)), /*#__PURE__*/React.createElement("td", {
        className: "tr",
        style: {
          fontWeight: 700,
          color: r.nmh >= kt ? C.green : C.amber
        }
      }, r.nmh.toFixed(1))));
    })())))), /*#__PURE__*/React.createElement("div", {
      className: "g2",
      style: {
        flex: 1
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "card",
      style: {
        flex: 1,
        borderColor: "rgba(245,158,11,.2)"
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "ch"
    }, /*#__PURE__*/React.createElement("div", {
      className: "ct"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cdot",
      style: {
        background: C.amber
      }
    }), "Net M/h Operator — by ", craneGroupBy === 'day' ? 'Day' : craneGroupBy === 'week' ? 'Week' : craneGroupBy === 'month' ? 'Month' : 'Quarter'), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 4
      }
    }, /*#__PURE__*/React.createElement("select", {
      value: selectedCrane,
      onChange: e => {
        setSelectedCrane(e.target.value);
        setQcPg(0);
      },
      style: {
        background: 'var(--bg3)',
        border: '1px solid var(--br2)',
        color: 'var(--t2)',
        fontSize: 10,
        borderRadius: 4,
        padding: '2px 6px',
        outline: 'none',
        fontFamily: 'inherit',
        cursor: 'pointer'
      }
    }, craneIds.map(c => /*#__PURE__*/React.createElement("option", {
      key: c,
      value: c
    }, c === 'ALL' ? 'Tất cả cần trục' : c))), /*#__PURE__*/React.createElement("select", {
      value: craneGroupBy,
      onChange: e => setCraneGroupBy(e.target.value),
      style: {
        background: 'var(--bg3)',
        border: '1px solid var(--br2)',
        color: 'var(--t2)',
        fontSize: 10,
        borderRadius: 4,
        padding: '2px 6px',
        outline: 'none',
        fontFamily: 'inherit',
        cursor: 'pointer'
      }
    }, /*#__PURE__*/React.createElement("option", {
      value: "day"
    }, "Theo ngày"), /*#__PURE__*/React.createElement("option", {
      value: "week"
    }, "Theo tuần"), /*#__PURE__*/React.createElement("option", {
      value: "month"
    }, "Theo tháng"), /*#__PURE__*/React.createElement("option", {
      value: "quarter"
    }, "Theo quý")))), /*#__PURE__*/React.createElement("div", {
      className: "cb",
      style: {
        height: 190
      }
    }, /*#__PURE__*/React.createElement(QCBarChart, {
      data: groupedChartDataOp,
      theme: theme
    }))), /*#__PURE__*/React.createElement("div", {
      className: "card",
      style: {
        flex: 1
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "ch"
    }, /*#__PURE__*/React.createElement("div", {
      className: "ct"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cdot",
      style: {
        background: C.amber
      }
    }), "Chi tiết từng ca — Điều chỉnh Operator"), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 9.5,
        color: "var(--t3)"
      }
    }, selectedCrane === 'ALL' ? qcOpData.length + ' records' : selectedCrane)), /*#__PURE__*/React.createElement("div", {
      className: "tw"
    }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "QC"), /*#__PURE__*/React.createElement("th", null, "Tàu"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Gross h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Net h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right",
        color: C.amber
      }
    }, "Stop h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Conts"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "G M/h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right",
        color: C.green
      }
    }, "N M/h ★"))), /*#__PURE__*/React.createElement("tbody", null, activeQcPageRows.map((q, i) => /*#__PURE__*/React.createElement("tr", {
      key: i
    }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("span", {
      className: "bx bc_",
      style: {
        fontFamily: "var(--mono)"
      }
    }, q.qc)), /*#__PURE__*/React.createElement("td", {
      className: "tb",
      style: {
        maxWidth: 120,
        overflow: "hidden",
        textOverflow: "ellipsis"
      }
    }, q.vessel), /*#__PURE__*/React.createElement("td", {
      className: "tr"
    }, q.gH.toFixed(1)), /*#__PURE__*/React.createElement("td", {
      className: "tr"
    }, q.nH.toFixed(1)), /*#__PURE__*/React.createElement("td", {
      className: "tr",
      style: {
        color: C.amber,
        fontWeight: 600
      }
    }, q.dH.toFixed(1)), /*#__PURE__*/React.createElement("td", {
      className: "tr tb"
    }, q.tot), /*#__PURE__*/React.createElement("td", {
      className: "tr"
    }, q.gmh.toFixed(1)), /*#__PURE__*/React.createElement("td", {
      className: "tr",
      style: {
        fontWeight: 700,
        color: q.nmh >= kt ? C.green : C.amber
      }
    }, q.nmh.toFixed(1))))))), totalPages > 1 && /*#__PURE__*/React.createElement("div", {
      className: "pgr"
    }, /*#__PURE__*/React.createElement("span", {
      className: "pgi"
    }, qcPg * qcPerPage + 1, "–", Math.min((qcPg + 1) * qcPerPage, filteredQcOp.length), " of ", filteredQcOp.length), /*#__PURE__*/React.createElement("button", {
      className: "pb",
      onClick: () => setQcPg(p => p - 1),
      disabled: qcPg === 0
    }, "‹"), renderPageButtons(qcPg, totalPages, setQcPg), /*#__PURE__*/React.createElement("button", {
      className: "pb",
      onClick: () => setQcPg(p => p + 1),
      disabled: qcPg >= totalPages - 1
    }, "›")))));
  })(), nav === "delays" && (() => {
    const critCount = delays.filter(d => d.dur >= 1).length;
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      className: "kg k4"
    }, /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Total Events",
      val: delays.length,
      ic: C.red,
      icon: "⚠",
      dl: "events",
      dlt: "neg",
      spark: sp.de
    }), /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Total Hours",
      val: kpi.tdHrs.toFixed(1),
      unit: "h",
      ic: C.amber,
      icon: "⏱",
      dl: "total",
      dlt: "neg",
      spark: sp.dh
    }), /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Terminal %",
      val: `${kpi.tcPct}%`,
      ic: C.purple,
      icon: "⚡",
      dl: "of all delays",
      dlt: "pos",
      spark: sp.de
    }), /*#__PURE__*/React.createElement(KpiCard, {
      lbl: "Avg/Vessel",
      val: kpi.avgDly.toFixed(1),
      unit: "h",
      ic: C.green,
      icon: "📉",
      dl: "per vessel",
      dlt: "pos",
      spark: sp.dl
    })), /*#__PURE__*/React.createElement("div", {
      className: "g32",
      style: {
        flex: 1
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "card",
      style: {
        flex: 1
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "ch"
    }, /*#__PURE__*/React.createElement("div", {
      className: "ct"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cdot",
      style: {
        background: C.red
      }
    }), "Delay Summary by Vessel"), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 9.5,
        color: "var(--t3)"
      }
    }, vesselDelayMap.length, " vessels")), /*#__PURE__*/React.createElement("div", {
      className: "tw"
    }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "Vessel"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Events"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Critical"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Total h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Terminal h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Non-Term h"), /*#__PURE__*/React.createElement("th", {
      style: {
        textAlign: "right"
      }
    }, "Force Maj h"))), /*#__PURE__*/React.createElement("tbody", null, vesselDelayMap.map((r, i) => /*#__PURE__*/React.createElement("tr", {
      key: i
    }, /*#__PURE__*/React.createElement("td", {
      className: "tb",
      style: {
        maxWidth: 140,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      }
    }, r.vessel), /*#__PURE__*/React.createElement("td", {
      className: "tr"
    }, r.events), /*#__PURE__*/React.createElement("td", {
      className: "tr"
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        color: r.critical > 0 ? C.red : C.amber,
        fontWeight: r.critical > 0 ? 700 : 400
      }
    }, r.critical)), /*#__PURE__*/React.createElement("td", {
      className: "tr"
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontWeight: 700,
        color: r.total >= 2 ? C.red : C.amber
      }
    }, r.total.toFixed(1))), /*#__PURE__*/React.createElement("td", {
      className: "tr",
      style: {
        color: C.red
      }
    }, r.terminal.toFixed(1)), /*#__PURE__*/React.createElement("td", {
      className: "tr",
      style: {
        color: C.amber
      }
    }, r.nonTerminal.toFixed(1)), /*#__PURE__*/React.createElement("td", {
      className: "tr",
      style: {
        color: C.purple
      }
    }, r.force.toFixed(1)))))))), /*#__PURE__*/React.createElement("div", {
      className: "gcol",
      style: {
        flex: 1,
        gap: 8
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "card"
    }, /*#__PURE__*/React.createElement("div", {
      className: "ch"
    }, /*#__PURE__*/React.createElement("div", {
      className: "ct"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cdot",
      style: {
        background: C.amber
      }
    }), "Breakdown by Type")), /*#__PURE__*/React.createElement("div", {
      className: "cb",
      style: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '8px 12px'
      }
    }, delays.length ? /*#__PURE__*/React.createElement(DonutChart, {
      data: delays,
      theme: theme
    }) : /*#__PURE__*/React.createElement("div", {
      style: {
        color: 'var(--t4)',
        fontSize: 11,
        padding: 8
      }
    }, "No delay data"))), /*#__PURE__*/React.createElement("div", {
      className: "card",
      style: {
        flex: 1,
        display: 'flex',
        flexDirection: 'column'
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "ch"
    }, /*#__PURE__*/React.createElement("div", {
      className: "ct"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cdot",
      style: {
        background: C.purple
      }
    }), "Top Delay Reasons")), /*#__PURE__*/React.createElement("div", {
      style: {
        padding: '4px 12px 12px',
        overflowY: 'auto',
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between'
      }
    }, /*#__PURE__*/React.createElement("div", null, Object.entries(delays.reduce((acc, d) => {
      const k = d.cat || d.type || 'Unknown';
      acc[k] = (acc[k] || 0) + d.dur;
      return acc;
    }, {})).sort(([, a], [, b]) => b - a).slice(0, 8).map(([lbl, h], i) => {
      const pct = kpi.tdHrs > 0 ? Math.round(h / kpi.tdHrs * 100) : 0;
      const friendlyLabels = {
        "Stop - 1": "Stop - 1: Crane & Technical (Kỹ thuật / Cẩu)",
        "Stop - 2": "Stop - 2: Cargo & Vessel (Tàu / Hàng hóa)",
        "Stop - 3": "Stop - 3: Bad Weather (Thời tiết xấu)"
      };
      const displayLbl = friendlyLabels[lbl] || lbl;
      return /*#__PURE__*/React.createElement("div", {
        key: i,
        style: {
          padding: '5px 0',
          borderBottom: '1px solid var(--br)'
        }
      }, /*#__PURE__*/React.createElement("div", {
        style: {
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 3
        }
      }, /*#__PURE__*/React.createElement("span", {
        style: {
          fontSize: 10.5,
          color: 'var(--t2)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          maxWidth: 240
        },
        title: displayLbl
      }, displayLbl), /*#__PURE__*/React.createElement("span", {
        style: {
          fontSize: 10.5,
          fontWeight: 700,
          color: h >= 1 ? C.red : C.amber,
          flexShrink: 0,
          marginLeft: 6
        }
      }, h.toFixed(1), "h")), /*#__PURE__*/React.createElement("div", {
        style: {
          height: 3,
          background: 'var(--br2)',
          borderRadius: 2
        }
      }, /*#__PURE__*/React.createElement("div", {
        style: {
          height: '100%',
          width: pct + '%',
          background: h >= 1 ? C.red : C.amber,
          borderRadius: 2,
          transition: 'width .3s'
        }
      })));
    })), /*#__PURE__*/React.createElement("div", {
      style: {
        marginTop: 16,
        paddingTop: 12,
        borderTop: '1px dashed var(--br2)',
        display: 'flex',
        flexDirection: 'column',
        gap: 6
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 9.5,
        fontWeight: 700,
        color: 'var(--t3)',
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        marginBottom: 2,
        display: 'flex',
        alignItems: 'center',
        gap: 4
      }
    }, /*#__PURE__*/React.createElement("span", null, "💡"), " Chi tiết phân loại dừng máy / Stop Categories Guide"), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        flexDirection: 'column',
        gap: 5
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        background: 'var(--bg3)',
        border: '1px solid var(--br2)',
        borderRadius: 6,
        padding: '6px 8px',
        display: 'flex',
        flexDirection: 'column',
        gap: 2
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 6
      }
    }, /*#__PURE__*/React.createElement("span", {
      className: "bx br_",
      style: {
        fontSize: 8.5,
        padding: '1px 5px'
      }
    }, "Stop - 1"), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10.5,
        fontWeight: 700,
        color: 'var(--t1)'
      }
    }, "Crane & Technical / Kỹ thuật cảng")), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 9.5,
        color: 'var(--t3)',
        lineHeight: 1.4
      }
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, "VI:"), " Sự cố kỹ thuật cẩu bờ: Hư ngáng, vướng cellguide, mất điện cẩu, bảo dưỡng, dịch chuyển cẩu hoặc đụng chân cần."), /*#__PURE__*/React.createElement("div", {
      style: {
        fontStyle: 'italic',
        opacity: 0.8,
        marginTop: 1
      }
    }, /*#__PURE__*/React.createElement("strong", null, "EN:"), " Quay Crane technical & terminal issues: Spreader damage, cellguide jam, power failure, maintenance, shifting, or leg collision."))), /*#__PURE__*/React.createElement("div", {
      style: {
        background: 'var(--bg3)',
        border: '1px solid var(--br2)',
        borderRadius: 6,
        padding: '6px 8px',
        display: 'flex',
        flexDirection: 'column',
        gap: 2
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 6
      }
    }, /*#__PURE__*/React.createElement("span", {
      className: "bx ba_",
      style: {
        fontSize: 8.5,
        padding: '1px 5px'
      }
    }, "Stop - 2"), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10.5,
        fontWeight: 700,
        color: 'var(--t1)'
      }
    }, "Cargo & Vessel / Chờ hàng & Tàu")), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 9.5,
        color: 'var(--t3)',
        lineHeight: 1.4
      }
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, "VI:"), " Chờ đợi do tàu hoặc kế hoạch: Chờ hàng hóa/chờ sà lan, chờ đo dầu tàu, chờ cân chỉnh mớn nước, tàu sửa nắp hầm."), /*#__PURE__*/React.createElement("div", {
      style: {
        fontStyle: 'italic',
        opacity: 0.8,
        marginTop: 1
      }
    }, /*#__PURE__*/React.createElement("strong", null, "EN:"), " Waiting for vessel or operational planning: Waiting for cargo/barge, vessel fuel measurement, draft adjustment, hatch cover repair."))), /*#__PURE__*/React.createElement("div", {
      style: {
        background: 'var(--bg3)',
        border: '1px solid var(--br2)',
        borderRadius: 6,
        padding: '6px 8px',
        display: 'flex',
        flexDirection: 'column',
        gap: 2
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 6
      }
    }, /*#__PURE__*/React.createElement("span", {
      className: "bx bp_",
      style: {
        fontSize: 8.5,
        padding: '1px 5px'
      }
    }, "Stop - 3"), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10.5,
        fontWeight: 700,
        color: 'var(--t1)'
      }
    }, "Force Majeure / Thời tiết & Bất khả kháng")), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 9.5,
        color: 'var(--t3)',
        lineHeight: 1.4
      }
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, "VI:"), " Nguyên nhân thời tiết xấu: Tạm dừng làm hàng do mưa lớn, gió giật mạnh, giông bão để bảo đảm an toàn."), /*#__PURE__*/React.createElement("div", {
      style: {
        fontStyle: 'italic',
        opacity: 0.8,
        marginTop: 1
      }
    }, /*#__PURE__*/React.createElement("strong", null, "EN:"), " Severe weather & force majeure: Operations suspended due to heavy rain, strong wind gusts, or storms to ensure safety."))))))))));
  })(), nav === "config" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "kg k4"
  }, [{
    lbl: "API Status",
    val: dbStatus === "healthy" ? "Healthy" : "CSV Fallback",
    ic: dbStatus === "healthy" ? C.green : C.amber,
    icon: "✓"
  }, {
    lbl: "Total Records",
    val: `${vessels.length} vessels · ${qcData.length} QC`,
    ic: C.blue,
    icon: "🗄"
  }, {
    lbl: "Report Date",
    val: reportDate || "—",
    ic: C.cyan,
    icon: "⏱"
  }, {
    lbl: "KPI Target",
    val: kt,
    unit: "M/h",
    ic: C.purple,
    icon: "🎯"
  }].map(k => /*#__PURE__*/React.createElement("div", {
    key: k.lbl,
    className: "kc"
  }, /*#__PURE__*/React.createElement("div", {
    className: "kc-top"
  }, /*#__PURE__*/React.createElement("div", {
    className: "kc-lbl"
  }, k.lbl), /*#__PURE__*/React.createElement("div", {
    className: "kc-ico",
    style: {
      background: `${k.ic}18`
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: k.ic
    }
  }, k.icon))), /*#__PURE__*/React.createElement("div", {
    className: "kc-val",
    style: {
      fontSize: 16
    }
  }, k.val, k.unit && /*#__PURE__*/React.createElement("span", null, k.unit))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "2fr 3fr",
      gap: 8,
      flex: 1,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "gcol"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.green
    }
  }), "System Status"), /*#__PURE__*/React.createElement("span", {
    className: "bx bg_"
  }, "Healthy")), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      padding: "4px 12px"
    }
  }, [["API Status", dbStatus === "healthy" ? "Healthy" : "CSV Fallback", dbStatus === "healthy" ? C.green : C.amber], ["Version", metaVer, "var(--t1)"], ["Database", dbStatus === "healthy" ? "SQLite connected" : "CSV fallback", dbStatus === "healthy" ? C.green : C.amber], ["KPI Target", `${kt} moves/h`, C.blue], ["Input Dir", "./data_input/", "var(--t2)"], ["Output Dir", "./outputs/", "var(--t2)"], ["Report Date", reportDate || "—", "var(--t2)"], ["Vessels", `${vessels.length} loaded`, "var(--t2)"], ["QC Records", `${qcData.length} loaded`, "var(--t2)"], ["Delay Events", `${delays.length} loaded`, delays.length > 0 ? C.amber : "var(--t2)"]].map(([k, v, c]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    className: "ms"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ms-l"
  }, k), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 600,
      color: c,
      fontFamily: k.includes("Dir") ? "var(--mono)" : "inherit"
    }
  }, v))))), /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: C.blue
    }
  }), "REST API Endpoints")), /*#__PURE__*/React.createElement("div", {
    className: "cb",
    style: {
      padding: "4px 12px"
    }
  }, [["GET", "/", "Dashboard HTML"], ["GET", "/api/meta", "Meta & config"], ["GET", "/api/data", "All dashboard data"], ["GET", "/api/vessels", "Vessel summary (legacy)"]].map(([m, ep, desc]) => /*#__PURE__*/React.createElement("div", {
    key: ep,
    className: "ms"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 8,
      fontWeight: 700,
      padding: "1px 5px",
      borderRadius: 3,
      background: "rgba(16,185,129,.12)",
      color: C.green,
      fontFamily: "var(--mono)"
    }
  }, m), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--mono)",
      fontSize: 10,
      color: C.cyan
    }
  }, ep)), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9,
      color: "var(--t4)"
    }
  }, desc)))))), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      display: "flex",
      flexDirection: "column",
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "ch"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ct"
  }, /*#__PURE__*/React.createElement("div", {
    className: "cdot",
    style: {
      background: "var(--t4)"
    }
  }), "System Log Viewer"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginLeft: "auto",
      background: "var(--bg0)",
      border: "1px solid var(--br2)",
      padding: 2,
      borderRadius: 6,
      display: "flex",
      gap: 2
    }
  }, ["ALL", "INFO", "WARN", "ERROR"].map(lvl => {
    const colors = {
      ALL: {
        bg: "rgba(90,116,143,.15)",
        c: "#8FA3BC",
        b: "#5A748F"
      },
      INFO: {
        bg: "rgba(59,130,246,.15)",
        c: "#3B82F6",
        b: "#3B82F6"
      },
      WARN: {
        bg: "rgba(245,158,11,.15)",
        c: "#F59E0B",
        b: "#F59E0B"
      },
      ERROR: {
        bg: "rgba(239,68,68,.15)",
        c: "#EF4444",
        b: "#EF4444"
      }
    };
    const active = logFilter === lvl;
    const current = colors[lvl];
    return /*#__PURE__*/React.createElement("button", {
      key: lvl,
      onClick: () => setLogFilter(lvl),
      style: {
        padding: "2px 8px",
        borderRadius: 4,
        fontSize: 9,
        fontWeight: 700,
        fontFamily: "'Inter', sans-serif",
        cursor: "pointer",
        border: active ? `1px solid ${current.b}` : "1px solid transparent",
        background: active ? current.bg : "transparent",
        color: active ? current.c : "#5A748F",
        transition: "all .12s",
        outline: "none"
      }
    }, lvl);
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflowY: "auto",
      background: "var(--bg0)",
      borderRadius: "0 0 7px 7px",
      padding: "8px 12px",
      fontFamily: "var(--mono)",
      minHeight: 0
    }
  }, (logFilter === "ALL" ? feedLines : feedLines.filter(l => l.lv === logFilter)).map((l, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "feed-line"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fl-t"
  }, l.t), /*#__PURE__*/React.createElement("span", {
    className: "fl-lv",
    style: {
      color: {
        INFO: C.blue,
        WARN: C.amber,
        ERROR: C.red,
        SUCCESS: C.green
      }[l.lv] || "var(--t3)"
    }
  }, "[", l.lv, "]"), /*#__PURE__*/React.createElement("span", {
    className: "fl-m"
  }, l.m)))))))), isMobile ? /*#__PURE__*/React.createElement(MobileBottomNav, {
    nav: nav,
    setNav: setNav,
    delayCount: delays.length
  }) : /*#__PURE__*/React.createElement(SystemFeed, {
    open: feed,
    onToggle: () => setFeed(o => !o),
    initLines: feedLines
  }))));
}
ReactDOM.createRoot(document.getElementById("root")).render(/*#__PURE__*/React.createElement(App, null));
