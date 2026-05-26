module ApplicationHelper
    def nav_link(label, path)
      active = current_page?(path)
      classes = active \
        ? "px-3 py-1.5 text-sm font-medium text-[#1a1a1a] border-b-2 border-[#1a1a1a]"
        : "px-3 py-1.5 text-sm text-[#888] hover:text-[#1a1a1a] transition-colors"
      link_to label, path, class: classes
    end
  
    def delay_color(prob)
      if prob > 0.5 then "#c0392b"
      elsif prob > 0.25 then "#c8902a"
      else "#4a8c5c"
      end
    end
  
    def fmt_pct(prob)
      "#{(prob * 100).round}%"
    end
end