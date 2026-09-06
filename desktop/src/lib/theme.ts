export type Theme = "dark" | "light";

export const THEME_KEY = "voxlabs-theme";

export function readTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  try {
    return localStorage.getItem(THEME_KEY) === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.toggle("light", theme === "light");
  root.style.colorScheme = theme;
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* ignore quota / private mode */
  }
}

export const THEME_BOOTSTRAP = `(function(){try{var q=new URLSearchParams(location.search).get('theme');var t=(q==='light'||q==='dark')?q:localStorage.getItem('${THEME_KEY}');if(t==='light'){document.documentElement.classList.add('light');document.documentElement.style.colorScheme='light'}else{document.documentElement.style.colorScheme='dark'}}catch(e){}})();`;
