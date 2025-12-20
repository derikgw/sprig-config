# Snyk GitLab CI/CD Integration Setup

This guide walks you through integrating Snyk into your GitLab CI/CD pipeline.

---

## Prerequisites

- A Snyk account (free tier works fine)
- GitLab project with CI/CD enabled
- Admin or maintainer access to your GitLab project

---

## Step 1: Get Your Snyk API Token

1. Log in to [Snyk](https://app.snyk.io/)
2. Click your profile icon → **Account Settings**
3. Navigate to **API Token** section
4. Click **Click to show** to reveal your token
5. Copy the token (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

**Important**: Keep this token secure! It grants access to your Snyk account.

---

## Step 2: Add Snyk Token to GitLab CI/CD Variables

### Via GitLab UI:

1. Go to your GitLab project
2. Navigate to **Settings → CI/CD**
3. Expand **Variables** section
4. Click **Add variable**
5. Configure:
   - **Key**: `SNYK_TOKEN`
   - **Value**: Your Snyk API token (from Step 1)
   - **Type**: `Variable`
   - **Flags**:
     - ✅ **Protect variable** (recommended - only available on protected branches)
     - ✅ **Mask variable** (prevents token from appearing in job logs)
     - ❌ **Expand variable reference** (leave unchecked)
6. Click **Add variable**

### Optional: Add Snyk Organization ID

If you have multiple Snyk organizations:

1. In Snyk, go to **Settings → General**
2. Copy your **Organization ID**
3. Add another GitLab CI/CD variable:
   - **Key**: `SNYK_ORG`
   - **Value**: Your Snyk Organization ID
   - **Flags**: No special flags needed

---

## Step 3: Verify Integration

1. Push a commit to a branch or create a merge request
2. Go to **CI/CD → Pipelines**
3. Click the latest pipeline
4. In the **security** stage, you should see:
   - ✅ `bandit` - Python code security scan
   - ✅ `snyk_test` - Dependency vulnerability scan
   - ✅ `snyk_code` - Code security analysis (optional)
   - ✅ `sast` - GitLab SAST
   - ✅ `secret_detection` - GitLab secret detection

---

## Understanding the Jobs

### `bandit` Job
- **What**: Scans Python code for security issues
- **Checks**: Hardcoded passwords, SQL injection patterns, insecure crypto, etc.
- **Output**: `bandit-report.json` artifact

### `snyk_test` Job
- **What**: Scans dependencies (from `poetry.lock`) for known vulnerabilities
- **Checks**: CVEs in packages, license compliance
- **Output**: `snyk-report.json` artifact
- **Dashboard**: Results appear in your Snyk dashboard via `snyk monitor`

### `snyk_code` Job (Optional)
- **What**: Static code analysis for security vulnerabilities
- **Checks**: OWASP Top 10, CWE issues, data flow analysis
- **Output**: `snyk-code-report.json` artifact

---

## Severity Thresholds

Currently set to `--severity-threshold=high`:
- **Critical**: Always fails
- **High**: Fails the job
- **Medium**: Reported but doesn't fail
- **Low**: Reported but doesn't fail

To make it stricter (fail on medium+):
```yaml
- snyk test --severity-threshold=medium
```

To make it more permissive (critical only):
```yaml
- snyk test --severity-threshold=critical
```

---

## Making Snyk Required (Blocking)

Currently, Snyk jobs have `allow_failure: true` so they won't block your pipeline.

To make them required:

```yaml
snyk_test:
  # Remove or comment out this line:
  # allow_failure: true
```

**Recommendation**: Keep `allow_failure: true` initially, review results, fix critical issues, then remove it.

---

## Viewing Results

### In GitLab:
1. Go to pipeline → Click the job → View logs
2. Download artifacts → Open JSON reports

### In Snyk Dashboard:
1. Log in to [Snyk](https://app.snyk.io/)
2. Navigate to **Projects**
3. Find `sprig-config-module`
4. View detailed vulnerability reports, fix recommendations, and trends

---

## Snyk Free Tier Limits

- ✅ 200 tests/month
- ✅ Unlimited private repos
- ✅ Basic vulnerability database
- ✅ CLI and CI/CD integration

If you exceed limits, Snyk will still work but with degraded features.

---

## Troubleshooting

### "Authentication failed"
- Verify `SNYK_TOKEN` is set correctly in GitLab CI/CD variables
- Check token hasn't expired (Snyk tokens don't expire by default)

### "Organization not found"
- If using `SNYK_ORG`, verify the organization ID is correct
- Or remove the `--org=$SNYK_ORG` flag from `.gitlab-ci.yml`

### "Poetry lock file not found"
- Ensure `poetry.lock` is committed to your repository
- Snyk needs it to analyze exact dependency versions

---

## Best Practices

1. **Start Permissive**: Use `allow_failure: true` initially
2. **Review Weekly**: Check Snyk dashboard for new vulnerabilities
3. **Fix Incrementally**: Focus on Critical → High → Medium
4. **Keep Updated**: Run `poetry update` regularly to get security patches
5. **Monitor Trends**: Use Snyk dashboard to track security posture over time

---

## Next Steps

- [ ] Set up `SNYK_TOKEN` in GitLab CI/CD variables
- [ ] Push a commit to trigger the pipeline
- [ ] Review results in Snyk dashboard
- [ ] Fix any critical/high severity issues
- [ ] Consider enabling Snyk PR checks (requires Snyk GitHub/GitLab integration)
- [ ] Set up Slack/email notifications for new vulnerabilities

---

## Additional Resources

- [Snyk CLI Documentation](https://docs.snyk.io/snyk-cli)
- [Snyk GitLab Integration](https://docs.snyk.io/integrations/git-repository-scm-integrations/gitlab-integration)
- [Bandit Documentation](https://bandit.readthedocs.io/)
