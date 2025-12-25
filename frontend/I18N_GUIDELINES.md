# Internationalization (i18n) Guidelines

## 🌍 Language Support

This app supports **English** and **Hebrew** with automatic RTL/LTR layout switching.

## ✅ Mandatory Rules for All Components

### 1. Import and Use the Language Hook
```typescript
import { useLanguage } from '../contexts/LanguageContext';

const MyComponent = () => {
  const { t } = useLanguage();
  // ...
};
```

### 2. NEVER Hardcode User-Facing Text
❌ **BAD**:
```typescript
<h1>Welcome to Recipe App</h1>
<button>Create Recipe</button>
<p>No recipes found</p>
```

✅ **GOOD**:
```typescript
<h1>{t('home.welcome')}</h1>
<button>{t('recipe.create.button')}</button>
<p>{t('recipe.list.empty')}</p>
```

### 3. Add Translation Keys to translations.ts

For every new text string, add BOTH English and Hebrew:

```typescript
// frontend/src/i18n/translations.ts
export const translations = {
  en: {
    "my.new.key": "My English text",
  },
  he: {
    "my.new.key": "הטקסט שלי בעברית",
  }
};
```

### 4. Use Semantic Key Names

Use descriptive, hierarchical keys:
- ✅ `recipe.form.title`
- ✅ `user.profile.edit`
- ✅ `error.network.timeout`
- ❌ `text1`, `label2`, `string3`

### 5. Test in Both Languages

Before committing:
1. Switch to English - verify all text displays correctly
2. Switch to Hebrew - verify all text displays correctly AND layout is RTL

### 6. Handle Dynamic Text

For text with variables, use string replacement:

```typescript
// In translations.ts
"recipe.delete.confirm": "Delete {title}?"

// In component
const message = t('recipe.delete.confirm').replace('{title}', recipe.title);
```

## 🎨 RTL-Aware Styling

Use Tailwind's `rtl:` modifier for directional styles:

```typescript
// Spacing
className="ml-4 rtl:mr-4 rtl:ml-0"
className="space-x-4 rtl:space-x-reverse"

// Text alignment
className="text-left rtl:text-right"

// Flex direction
className="flex-row rtl:flex-row-reverse"
```

## 📋 Pre-Commit Checklist

- [ ] All user-facing text uses `t()` function
- [ ] All translation keys exist in BOTH `en` and `he`
- [ ] Tested component in English
- [ ] Tested component in Hebrew
- [ ] RTL layout looks correct
- [ ] No hardcoded text in JSX
- [ ] No console errors related to missing translation keys

## 🔍 Common Mistakes

### Missing Translation Key
```typescript
const { t } = useLanguage();
return <h1>{t('missing.key')}</h1>; // Returns 'missing.key' as fallback
```
**Fix**: Add the key to `translations.ts`

### Forgot to Import Hook
```typescript
// ❌ Error: t is not defined
return <h1>{t('home.title')}</h1>;
```
**Fix**: `const { t } = useLanguage();`

### Hardcoded Text in Placeholders
```typescript
// ❌ BAD
<Input placeholder="Enter recipe name" />

// ✅ GOOD
<Input placeholder={t('recipe.form.title_placeholder')} />
```

## 📁 File Locations

- **Translations**: `frontend/src/i18n/translations.ts`
- **Language Context**: `frontend/src/contexts/LanguageContext.tsx`
- **Language Switcher**: `frontend/src/components/LanguageSwitcher.tsx`

## 🚀 Quick Start for New Components

```typescript
import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';

const MyNewComponent: React.FC = () => {
  const { t } = useLanguage();

  return (
    <div>
      <h1>{t('my.component.title')}</h1>
      <p>{t('my.component.description')}</p>
    </div>
  );
};

export default MyNewComponent;
```

Then add to `translations.ts`:
```typescript
en: {
  // ... existing keys
  "my.component.title": "My Component",
  "my.component.description": "This is my new component",
}
he: {
  // ... existing keys
  "my.component.title": "הרכיב שלי",
  "my.component.description": "זהו הרכיב החדש שלי",
}
```

## ➕ Adding a New Language

The current implementation can be easily extended to support additional languages. Here's how:

### Step 1: Add Language Type
In `frontend/src/contexts/LanguageContext.tsx`, update the `Language` type:

```typescript
// Before
type Language = 'en' | 'he';

// After (example: adding Spanish)
type Language = 'en' | 'he' | 'es';
```

### Step 2: Add Translations
In `frontend/src/i18n/translations.ts`, add a complete translation object:

```typescript
export const translations = {
  en: {
    "app.title": "Recipe App",
    // ... all English keys
  },
  he: {
    "app.title": "אפליקציית מתכונים",
    // ... all Hebrew keys
  },
  es: {  // NEW
    "app.title": "Aplicación de Recetas",
    // ... all Spanish keys (must match en/he keys exactly)
  }
};
```

**Important**: Every key in `en` must also exist in the new language object!

### Step 3: Update Language Switcher
In `frontend/src/components/LanguageSwitcher.tsx`, add the new language to the array:

```typescript
const languages = [
  { code: 'en' as const, label: 'English', flag: '🇬🇧' },
  { code: 'he' as const, label: 'עברית', flag: '🇮🇱' },
  { code: 'es' as const, label: 'Español', flag: '🇪🇸' },  // NEW
];
```

### Step 4: Configure Direction (if RTL)
If the new language is RTL (like Arabic), update the direction logic in `LanguageContext.tsx`:

```typescript
useEffect(() => {
  // Add your RTL language code here
  const dir = ['he', 'ar', 'fa'].includes(language) ? 'rtl' : 'ltr';
  setDirection(dir);
  document.documentElement.dir = dir;
  document.documentElement.lang = language;
}, [language]);
```

### Step 5: Test
1. Select the new language from the switcher
2. Verify all text displays correctly
3. Check that layout direction is correct (LTR/RTL)
4. Ensure no missing translation keys (check browser console)

### Common RTL Languages
- Arabic (`ar`) 🇸🇦
- Hebrew (`he`) 🇮🇱
- Persian/Farsi (`fa`) 🇮🇷
- Urdu (`ur`) 🇵🇰

### Common LTR Languages
- Spanish (`es`) 🇪🇸
- French (`fr`) 🇫🇷
- German (`de`) 🇩🇪
- Italian (`it`) 🇮🇹
- Russian (`ru`) 🇷🇺
- Chinese (`zh`) 🇨🇳
- Japanese (`ja`) 🇯🇵

---

**Remember**: Every string a user sees should go through the `t()` function!

