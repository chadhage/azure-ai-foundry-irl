# Microsoft product icon attribution and permitted use

The SVG files in this directory are Microsoft product artwork, not Azure Foundry IRL
branding. Microsoft retains its rights to this artwork.

Microsoft permits copying, distribution and display of these icons in
architectural diagrams, training materials and documentation. Other uses require
the applicable permission. Do not crop, flip, rotate, recolor, distort or use a
product icon to represent this project's own application or fictional entities.

## Official sources

- [Azure Architecture Center icon terms and V24 download](https://learn.microsoft.com/azure/architecture/icons/)
- [Microsoft Fabric icon terms and official download](https://learn.microsoft.com/fabric/fundamentals/icons)
- [Pinned Microsoft Fabric source archive](https://raw.githubusercontent.com/microsoft/fabric-samples/564ec4139742b838468fcf8aa44dac4afe02ce92/docs-samples/Icons.zip)

The approved package URLs, SHA-256 digests and exact selected ZIP entries are in
[`architecture-atlas.json`](../../../data/architecture-atlas.json).
[`provenance.json`](provenance.json) records each imported file's digest.

Imported SVG bytes are unchanged. Diagram rendering preserves the original
artwork's aspect ratio and colors. Git attributes prevent line-ending conversion
for these assets so provenance hashes survive Windows checkouts. Product names
appear next to their icons.
Generic visitor, application-policy, publication-gate and business-entity nodes
deliberately have no Microsoft product icon.

The Fabric package supplies the official Fabric, lakehouse, pipeline and Purview
icons; the Azure package supplies Azure and Foundry service icons. The Fabric
product icon identifies the Fabric IQ context, not a claim that a dedicated
ontology icon or deployed ontology exists.

## Reproduce the import

After reviewing the current Microsoft terms:

```powershell
.\.venv\Scripts\python.exe scripts\build_architecture_atlas.py --import-icons
```

The importer accepts only the pinned archive digests. A changed upstream package
fails explicitly and requires review. It does not silently substitute icons.

These are educational reference diagrams, not Microsoft endorsement or a
representation of this repository as a Microsoft product.
