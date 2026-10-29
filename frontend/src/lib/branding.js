export const DEFAULT_BRANDING = { company_name: "McCoy Trucking", primary_color: "#3b82f6", accent_color: "#dc2626", dark_background: "#0b0f17", light_background: "#f5f7fa" };
const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const mix = (hex, target, amount) => `#${rgb(hex).map((v, i) => Math.round(v * (1 - amount) + rgb(target)[i] * amount).toString(16).padStart(2, "0")).join("")}`;
const luminance = (hex) => rgb(hex).map((v) => v / 255).map((v) => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4).reduce((a, v, i) => a + v * [.2126, .7152, .0722][i], 0);
export const contrastText = (hex) => luminance(hex) > .179 ? "#10141c" : "#ffffff";
export const inkColor = (hex, dark = false) => {
  let value = hex;
  for (let i = 0; i < 12 && (dark ? luminance(value) < .45 : luminance(value) > .16); i++) value = mix(value, dark ? "#ffffff" : "#000000", .16);
  return value;
};
export const hslValue = (hex) => {
  const [r, g, b] = rgb(hex).map((v) => v / 255), max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min, l = (max + min) / 2;
  const s = !d ? 0 : d / (1 - Math.abs(2 * l - 1));
  let h = !d ? 0 : max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
  h = (h * 60 + 360) % 360;
  return `${h.toFixed(1)} ${(s * 100).toFixed(1)}% ${(l * 100).toFixed(1)}%`;
};
export const brandingVariables = (brand, theme) => {
  const dark = theme === "dark", bg = dark ? brand.dark_background : brand.light_background;
  return { "--background": hslValue(bg), "--card": hslValue(mix(bg, dark ? "#ffffff" : "#ffffff", dark ? .035 : .65)), "--popover": hslValue(mix(bg, "#ffffff", dark ? .045 : .9)),
    "--primary": hslValue(brand.primary_color), "--primary-foreground": hslValue(contrastText(brand.primary_color)), "--ring": hslValue(brand.primary_color),
    "--brand-primary": brand.primary_color, "--brand-accent": brand.accent_color, "--brand-ink": inkColor(brand.primary_color, dark), "--brand-accent-ink": inkColor(brand.accent_color, dark),
    "--brand-primary-text": contrastText(brand.primary_color), "--brand-accent-text": contrastText(brand.accent_color),
    "--brand-print-primary": inkColor(brand.primary_color), "--brand-print-accent": inkColor(brand.accent_color) };
};