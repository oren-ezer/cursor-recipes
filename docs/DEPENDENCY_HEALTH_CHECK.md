# Dependency Health Check Report

Generated after 2-month break to assess dependency status.

## Summary

- ⚠️ **Security vulnerabilities found** in frontend dependencies
- 📦 **Many outdated packages** in both backend and frontend
- 🔴 **Critical**: OpenAI SDK has major version update (v1 → v2) - **BREAKING CHANGES**
- 🟡 **Action Required**: Update security-vulnerable packages

---

## Backend Dependencies (Python)

### Current Versions vs Latest

| Package | Current | Latest | Type | Priority |
|---------|---------|--------|------|----------|
| **openai** | 1.101.0 | **2.8.1** | 🔴 Major | **CRITICAL** - Breaking changes |
| **fastapi** | 0.116.0 | 0.123.4 | Minor | High |
| **pydantic** | 2.11.7 | 2.12.5 | Patch | Medium |
| **alembic** | 1.16.3 | 1.17.2 | Minor | Medium |
| **cryptography** | 45.0.5 | 46.0.3 | Minor | High (security) |
| **psycopg2-binary** | 2.9.10 | 2.9.11 | Patch | Low |
| **bcrypt** | 4.0.1 | 5.0.0 | Major | Medium - Review breaking changes |

### Key Backend Updates Needed

1. **OpenAI SDK (v1 → v2)**: ⚠️ **MAJOR BREAKING CHANGES**
   - Current code uses `openai>=1.101.0`
   - Latest is `2.8.1` - completely different API
   - **Action**: Review OpenAI SDK v2 migration guide before updating
   - **Impact**: `AIService` class will need significant refactoring
   - **Migration**: See https://github.com/openai/openai-python/discussions/742

2. **FastAPI**: 0.116.0 → 0.123.4 (minor updates, should be safe)

3. **Pydantic**: 2.11.7 → 2.12.5 (patch updates, should be safe)

4. **bcrypt**: 4.0.1 → 5.0.0 (major version, check breaking changes)

### Backend Update Recommendations

**Safe to Update Now:**
- fastapi (minor version)
- pydantic (patch version)
- alembic (minor version)
- cryptography (security updates)
- psycopg2-binary (patch)

**Requires Review:**
- openai (major version - breaking changes)
- bcrypt (major version - check breaking changes)

---

## Frontend Dependencies (npm)

### Security Vulnerabilities Found 🔴

1. **@eslint/plugin-kit** - ReDoS vulnerability
   - **Severity**: Moderate
   - **Fix**: Update eslint to latest (9.39.1)
   - **Action**: `npm audit fix`

2. **@modelcontextprotocol/sdk** - DNS rebinding protection
   - **Severity**: High
   - **Fix**: Update to >=1.24.0
   - **Action**: `npm audit fix`

3. **body-parser** - DoS vulnerability
   - **Severity**: Moderate
   - **Fix**: Update to latest
   - **Action**: `npm audit fix`

4. **brace-expansion** - ReDoS vulnerability
   - **Severity**: Moderate
   - **Fix**: Update to latest
   - **Action**: `npm audit fix`

5. **glob** - Command injection
   - **Severity**: High ⚠️
   - **Fix**: Update to latest
   - **Action**: `npm audit fix`

6. **js-yaml** - Prototype pollution
   - **Severity**: Moderate
   - **Fix**: Update to latest
   - **Action**: `npm audit fix`

7. **vite** - Multiple vulnerabilities
   - **Severity**: Moderate
   - **Issues**: File serving, fs.deny bypass
   - **Fix**: Update to 6.4.1+ (or 7.x latest)
   - **Action**: `npm audit fix` or manual update

### Outdated Frontend Packages

**High Priority Updates:**
- `eslint`: 9.26.0 → 9.39.1 (security fix)
- `vite`: 6.3.5 → 6.4.1 (security fix) or 7.2.6 (latest)
- `react`: 19.1.0 → 19.2.0
- `react-dom`: 19.1.0 → 19.2.0

**Medium Priority:**
- `react-router-dom`: 7.6.0 → 7.10.0
- `typescript`: 5.8.3 → 5.9.3
- `typescript-eslint`: 8.32.0 → 8.48.1
- `tailwindcss`: 3.4.17 → 3.4.18 (minor) or 4.1.17 (major)
- `@vitejs/plugin-react`: 4.4.1 → 4.7.0 (or 5.1.1 major)

**Low Priority:**
- Various @radix-ui packages (minor updates)
- Testing library updates

---

## Recommended Action Plan

### Immediate (Security Fixes)

1. **Frontend Security Fixes**:
   ```bash
   cd frontend
   npm audit fix
   npm test  # Verify tests still pass
   ```

2. **Backend Security Updates**:
   ```bash
   cd backend
   uv sync --upgrade-package cryptography
   ```

### Short-term (Safe Updates)

3. **Backend Safe Updates**:
   ```bash
   cd backend
   uv sync --upgrade-package fastapi
   uv sync --upgrade-package pydantic
   uv sync --upgrade-package alembic
   uv run pytest tests/ -v  # Verify tests pass
   ```

4. **Frontend Safe Updates**:
   ```bash
   cd frontend
   npm update react react-dom react-router-dom
   npm test  # Verify tests still pass
   ```

### Medium-term (Breaking Changes Review)

5. **OpenAI SDK Migration** (v1 → v2):
   - Review migration guide: https://github.com/openai/openai-python/discussions/742
   - Test AI service functionality thoroughly
   - Update `AIService` class implementation
   - Update tests
   
   **Breaking Changes Include:**
   - API structure changes
   - Async/await patterns may differ
   - Response format changes

6. **bcrypt Major Update** (4.0.1 → 5.0.0):
   - Review changelog
   - Test authentication flows
   - Verify password hashing/verification still works

### Optional (Major Version Updates)

7. **Frontend Major Updates** (if needed):
   - `@vitejs/plugin-react`: 4.x → 5.x (review breaking changes)
   - `tailwindcss`: 3.x → 4.x (major rewrite, significant changes)
   - `vitest`: 3.x → 4.x (may require test updates)

---

## Testing After Updates

After any dependency updates, run:

**Backend:**
```bash
cd backend
uv run pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm run test:run
npm run build  # Verify build still works
```

**Integration:**
- Start backend: `uv run uvicorn src.main:app --reload`
- Start frontend: `npm run dev`
- Test basic flows (login, create recipe, view recipes)

---

## Notes

- **OpenAI SDK v2**: This is the most critical update requiring code changes. Consider doing this as a separate task.
- **Security fixes**: Should be prioritized, especially the high-severity glob command injection vulnerability.
- **Major versions**: Review changelogs and migration guides before updating.
- **Test thoroughly**: Always run full test suite after dependency updates.

---

## Next Steps

1. ✅ Review this report
2. ⬜ Apply security fixes (`npm audit fix` for frontend)
3. ⬜ Update safe backend packages
4. ⬜ Plan OpenAI SDK v2 migration (separate task)
5. ⬜ Run full test suite
6. ⬜ Test application manually

