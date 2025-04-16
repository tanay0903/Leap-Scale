!(function (e) {
  "object" == typeof exports && "object" == typeof module
    ? e(require("../../lib/codemirror"))
    : "function" == typeof define && define.amd
    ? define(["../../lib/codemirror"], e)
    : e(CodeMirror);
})(function (i) {
  "use strict";
  var a = "CodeMirror-activeline",
    s = "CodeMirror-activeline-background",
    c = "CodeMirror-activeline-gutter";
  function l(e) {
    for (var t = 0; t < e.state.activeLines.length; t++)
      e.removeLineClass(e.state.activeLines[t], "wrap", a),
        e.removeLineClass(e.state.activeLines[t], "background", s),
        e.removeLineClass(e.state.activeLines[t], "gutter", c);
  }
  function o(t, e) {
    for (var n = [], i = 0; i < e.length; i++) {
      var o = e[i],
        r = t.getOption("styleActiveLine");
      ("object" == typeof r && r.nonEmpty
        ? o.anchor.line == o.head.line
        : o.empty()) &&
        ((r = t.getLineHandleVisualStart(o.head.line)),
        n[n.length - 1] != r && n.push(r));
    }
    !(function (e, t) {
      if (e.length == t.length) {
        for (var n = 0; n < e.length; n++) if (e[n] != t[n]) return;
        return 1;
      }
    })(t.state.activeLines, n) &&
      t.operation(function () {
        l(t);
        for (var e = 0; e < n.length; e++)
          t.addLineClass(n[e], "wrap", a),
            t.addLineClass(n[e], "background", s),
            t.addLineClass(n[e], "gutter", c);
        t.state.activeLines = n;
      });
  }
  function r(e, t) {
    o(e, t.ranges);
  }
  i.defineOption("styleActiveLine", !1, function (e, t, n) {
    n = n != i.Init && n;
    t != n &&
      (n &&
        (e.off("beforeSelectionChange", r), l(e), delete e.state.activeLines),
      t &&
        ((e.state.activeLines = []),
        o(e, e.listSelections()),
        e.on("beforeSelectionChange", r)));
  });
});
