# Figure audit prompt

Audit the proposed overview figure for academic suitability.

Check:

- faithfulness to the manuscript;
- readability;
- clarity of labels;
- absence of decorative clutter;
- usefulness to the reader;
- fit with the manuscript narrative.

Also evaluate the following explicitly:

- Is there a dominant organizing idea?
- Is one panel visually dominant, with the rest serving as context or constraints?
- Is the information density appropriate for manuscript-scale reading?
- Is the figure understandable in about 15 seconds?
- Does the figure add synthesis rather than merely reflecting the section headings?
- If the route is `image_gen`, has the accepted generated image been selected rather than replaced by a code-rendered figure?
- Is the accepted overview figure inserted into Markdown and expected to carry through to TeX?

Hard reject conditions:

- dense wall-of-bullets boxes;
- many equal-sized boxes with little hierarchy;
- too many examples listed in each node;
- arrows with long labels or unclear semantics;
- diagram looks like a generic infographic;
- figure would be better as a table.

Return one of: `accept`, `revise`, or `reject`, with concrete reasons.
Save the result to `reports/figure_audit.md`.

If the result is `revise`, include precise revision instructions and explain whether the underlying issue is content selection, layout, or rendering quality.
