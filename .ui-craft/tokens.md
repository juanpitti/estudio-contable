# Token Spine — Estudio Contable

## Primitive Tokens

### Color — Neutral Ramp (cool tint)
```css
--gray-50:  oklch(98%  0.005 250);
--gray-100: oklch(96%  0.008 250);
--gray-200: oklch(91%  0.010 250);
--gray-300: oklch(82%  0.012 250);
--gray-400: oklch(70%  0.014 250);
--gray-500: oklch(58%  0.014 250);
--gray-600: oklch(46%  0.012 250);
--gray-700: oklch(36%  0.010 250);
--gray-800: oklch(26%  0.008 250);
--gray-900: oklch(18%  0.006 250);
--gray-950: oklch(12%  0.004 250);
```

### Color — Accent Ramp (Emerald, hue ~155)
```css
--accent-hue: 155;
--accent-50:  oklch(97%  0.03  var(--accent-hue));
--accent-100: oklch(93%  0.06  var(--accent-hue));
--accent-200: oklch(86%  0.10  var(--accent-hue));
--accent-300: oklch(76%  0.15  var(--accent-hue));
--accent-400: oklch(64%  0.19  var(--accent-hue));
--accent-500: oklch(52%  0.20  var(--accent-hue));
--accent-600: oklch(42%  0.18  var(--accent-hue));
--accent-700: oklch(32%  0.14  var(--accent-hue));
--accent-800: oklch(24%  0.10  var(--accent-hue));
--accent-900: oklch(16%  0.06  var(--accent-hue));
--accent-950: oklch(10%  0.03  var(--accent-hue));
```

### Color — Semantic Bases
```css
--green-400:  oklch(72%  0.18 145);
--green-600:  oklch(52%  0.18 145);
--amber-400:  oklch(78%  0.16 70);
--amber-600:  oklch(58%  0.16 70);
--red-400:    oklch(65%  0.20 25);
--red-600:    oklch(48%  0.20 25);
--blue-400:   oklch(66%  0.16 250);
--blue-600:   oklch(50%  0.16 250);
```

### Spacing — 8pt Scale
```css
--space-1:  0.25rem;  /* 4px */
--space-2:  0.5rem;   /* 8px */
--space-3:  0.75rem;  /* 12px */
--space-4:  1rem;     /* 16px */
--space-5:  1.25rem;  /* 20px */
--space-6:  1.5rem;   /* 24px */
--space-8:  2rem;     /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
--space-24: 6rem;     /* 96px */
```

### Type
```css
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;

--text-xs:   0.75rem;   /* 12px */
--text-sm:   0.875rem;  /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg:   1.125rem;  /* 18px */
--text-xl:   1.25rem;   /* 20px */
--text-2xl:  1.5rem;    /* 24px */
--text-3xl:  1.875rem;  /* 30px */
--text-4xl:  2.25rem;   /* 36px */

--font-light:   300;
--font-regular: 400;
--font-medium:  500;
--font-semibold: 600;
--font-bold:    700;

--leading-none:   1;
--leading-tight:  1.2;
--leading-snug:   1.35;
--leading-normal: 1.5;
--leading-relaxed: 1.65;

--tracking-tight:  -0.02em;
--tracking-normal: 0;
--tracking-wide:   0.01em;
```

### Radii
```css
--radius-none: 0;
--radius-sm:   0.375rem;  /* 6px */
--radius-md:   0.5rem;    /* 8px */
--radius-lg:   0.625rem;  /* 10px */
--radius-xl:   0.75rem;   /* 12px */
--radius-2xl:  1rem;      /* 16px */
--radius-full: 9999px;
```

### Shadows
```css
--shadow-sm:  0 1px 2px oklch(0% 0 0 / 0.04);
--shadow-md:  0 4px 6px oklch(0% 0 0 / 0.04),
              0 1px 2px oklch(0% 0 0 / 0.02);
--shadow-lg:  0 10px 15px oklch(0% 0 0 / 0.05),
              0 4px 6px oklch(0% 0 0 / 0.02);
```

### Motion
```css
--duration-instant: 80ms;
--duration-fast:    150ms;
--duration-normal:  250ms;
--duration-slow:    400ms;

--ease-out:    cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

## Semantic Tokens — Light Mode

```css
:root {
  --surface-canvas:  var(--gray-50);
  --surface-raised:  #ffffff;
  --surface-overlay: #ffffff;
  --surface-sunken:  var(--gray-100);
  --surface-inverse: var(--gray-900);

  --text-primary:    var(--gray-900);
  --text-secondary:  var(--gray-500);
  --text-tertiary:   var(--gray-400);
  --text-on-accent:  #fff;
  --text-on-inverse: var(--gray-50);
  --text-link:       var(--accent-600);

  --border-subtle:   oklch(0% 0 0 / 0.06);
  --border-default:  oklch(0% 0 0 / 0.10);
  --border-strong:   oklch(0% 0 0 / 0.20);
  --border-focus:    var(--accent-500);

  --accent-bg:        var(--accent-500);
  --accent-bg-hover:  var(--accent-600);
  --accent-bg-active: var(--accent-700);
  --accent-text:      #fff;

  --success-bg:     oklch(96% 0.03 145);
  --success-text:   var(--green-600);
  --success-border: var(--green-400);

  --warning-bg:     oklch(97% 0.03 70);
  --warning-text:   var(--amber-600);
  --warning-border: var(--amber-400);

  --error-bg:       oklch(97% 0.03 25);
  --error-text:     var(--red-600);
  --error-border:   var(--red-400);
}
```

## Semantic Tokens — Dark Mode

```css
[data-theme="dark"] {
  --surface-canvas:  oklch(10% 0.004 250);
  --surface-raised:  oklch(14% 0.006 250);
  --surface-overlay: oklch(18% 0.008 250);
  --surface-sunken:  oklch(8% 0.003 250);
  --surface-inverse: var(--gray-50);

  --text-primary:    var(--gray-100);
  --text-secondary:  var(--gray-400);
  --text-tertiary:   var(--gray-600);
  --text-on-inverse: var(--gray-900);
  --text-link:       var(--accent-400);

  --border-subtle:   oklch(100% 0 0 / 0.06);
  --border-default:  oklch(100% 0 0 / 0.10);
  --border-strong:   oklch(100% 0 0 / 0.20);

  /* Accent desaturates 12% in dark to prevent burn */
  --accent-bg:        oklch(52% 0.17 155);
  --accent-bg-hover:  oklch(58% 0.17 155);
  --accent-bg-active: oklch(64% 0.17 155);
}
```

## Component Tokens

### Button Primary
```css
--button-primary-bg:            var(--accent-bg);
--button-primary-bg-hover:      var(--accent-bg-hover);
--button-primary-bg-active:     var(--accent-bg-active);
--button-primary-text:          var(--accent-text);
--button-primary-border-radius: var(--radius-md);
--button-primary-padding-x:     var(--space-4);
--button-primary-padding-y:     var(--space-2);
```

### Input
```css
--input-bg:            var(--surface-raised);
--input-border:        var(--border-default);
--input-border-focus:  var(--border-focus);
--input-text:          var(--text-primary);
--input-placeholder:   var(--text-tertiary);
--input-border-radius: var(--radius-sm);
```

### Card
```css
--card-bg:            var(--surface-raised);
--card-border:        var(--border-subtle);
--card-border-radius: var(--radius-lg);
--card-padding:       var(--space-5);
```

### Sidebar
```css
--sidebar-bg:         var(--surface-sunken);
--sidebar-width:      240px;
--sidebar-collapsed:  56px;
--sidebar-border:     var(--border-subtle);
```
