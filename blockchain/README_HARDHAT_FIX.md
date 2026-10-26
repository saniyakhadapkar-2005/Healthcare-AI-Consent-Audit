# Hardhat setup

This project intentionally uses **Hardhat 2.22.19 + CommonJS**.

Do NOT add this to package.json:

```json
"type": "module"
```

The config, deploy script, and tests use CommonJS `require(...)`.

## Clean Windows setup

From this `blockchain` folder:

```powershell
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item package-lock.json -Force -ErrorAction SilentlyContinue
npm install
npm run compile
npm test
npm run node
```

If your terminal still reports that package.json contains `"type": "module"`, you are not using this package.json. Open the exact file shown by the error and remove that property, or delete the extracted folder and extract this ZIP again.

You can also run:

```text
verify_setup.bat
```

which checks the package before compiling.
