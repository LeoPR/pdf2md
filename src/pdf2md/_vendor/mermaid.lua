-- T190/e22: CodeBlock ```mermaid -> <pre class="mermaid"> para o mermaid.js
-- renderizar client-side no Chrome headless (mesmo mecanismo do KaTeX).
function CodeBlock(el)
  if el.classes:includes("mermaid") then
    return pandoc.RawBlock("html", "<pre class=\"mermaid\">\n" .. el.text .. "\n</pre>")
  end
end
