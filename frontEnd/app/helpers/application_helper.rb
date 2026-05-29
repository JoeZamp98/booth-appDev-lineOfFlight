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

    # Brand accent color per carrier. Falls back to the app's red accent so
    # carriers without a defined brand color keep the existing look.
    AIRLINE_COLORS = {
      "UA" => "#002C8C", # United blue
    }.freeze

    def airline_color(carrier)
      AIRLINE_COLORS.fetch(carrier.to_s, "#c0392b")
    end
  
    def fmt_pct(prob)
      "#{(prob * 100).round}%"
    end
end