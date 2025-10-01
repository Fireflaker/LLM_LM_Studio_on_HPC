# ⚠️ CRITICAL SAFETY WARNINGS FOR HPC

## 🚨 DATALAB PERMISSIONS WARNING

**DANGER**: The user `zwu09` may have write access to the ENTIRE `/cluster/tufts/datalab` directory, not just `/cluster/tufts/datalab/zwu09`.

### What This Means:

- Commands like `rm -rf` in `/cluster/tufts/datalab` could delete OTHER USERS' data
- This would be a CATASTROPHIC disaster affecting multiple research projects
- **NEVER** use wildcards or recursive operations above the `zwu09` subdirectory because HOME might be mounted to this "fake `datalab` home"

### Safe Practices:

✅ **ALWAYS work in**: `/cluster/tufts/datalab/zwu09/`
✅ **Use full paths for risky**: `rm /cluster/tufts/datalab/zwu09/specific_file`
✅ **Test with `ls` first**: Before any delete, list exactly what will be affected

❌ **NEVER do**:

```bash
cd /cluster/tufts/datalab
rm -rf *                    # CATASTROPHIC - deletes ALL users' data
rm -rf ./*                  # CATASTROPHIC - same as above
find . -delete              # CATASTROPHIC - recursive delete
```

❌ **NEVER use broad patterns in shared space**:

```bash
rm -rf /cluster/tufts/datalab/*.json   # Could delete other users' files
```

✅ **Safe Examples**:

```bash
# Always specify the zwu09 directory explicitly
rm -rf /cluster/tufts/datalab/zwu09/.cache
rm /cluster/tufts/datalab/zwu09/specific_file.txt

# Or cd into zwu09 first
cd /cluster/tufts/datalab/zwu09
rm -rf .cache  # Now safe - only affects zwu09 directory
```

### Before ANY Delete Command:

1. **List first**: `ls -la` to see exactly what will be affected
2. **Check pwd**: Verify you're in `/cluster/tufts/datalab/zwu09`
3. **Use full paths**: Include `/zwu09/` explicitly
4. **No wildcards**: Avoid `*` unless absolutely necessary and tested

---

## 🔒 Home Directory Quotas

**Your Home Directory**: `/cluster/home/zwu09`

- **Quota**: 30.7GB
- **Current usage**: ~11.7GB (19M in actual files, rest likely in hidden caches)
- **Available**: ~1kB

**DO NOT** store ANYTHING in home. Treat as if does not exsist. Redirect everything to datalab/zwu09

---

## 💾 Storage Summary

| Location                          | Type                   | Your Quota/Space               | Usage                       |
| --------------------------------- | ---------------------- | ------------------------------ | --------------------------- |
| `/cluster/home/zwu09`           | Depriciated, Read only | 30.7GB(0Gb)                    | 11.7GB(All used)            |
| `/cluster/tufts/datalab/zwu09`  | Shared pool            | Part of 2.3TB pool             | Safe to use                 |
| `/cluster/tufts/datalab` (root) | **DANGER ZONE**  | **CONTAINS OTHER USERS** | **NEVER DELETE HERE** |

---

## 📋 Pre-Delete Checklist

Before running ANY command that deletes files:

- [ ] I am in `/cluster/tufts/datalab/zwu09` or using full paths with `/zwu09/`
- [ ] I have run `ls` to verify exactly what will be affected
- [ ] The command does NOT use wildcards in `/cluster/tufts/datalab` root
- [ ] The command explicitly includes `zwu09` in the path
- [ ] I have tested the command with `echo` or `-n` (dry run) if available

---

**Last Updated**: 2025-09-30 Human profread/edited
**Severity**: CRITICAL - Data loss could affect multiple research projects
