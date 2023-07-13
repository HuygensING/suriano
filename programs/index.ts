import fs from 'fs'
import path from 'path'
import puppeteer from 'puppeteer'
import chalk from 'chalk'

function isXmlFile(dirent: fs.Dirent) {
	return dirent.isFile() && path.extname(dirent.name) === '.xml'
}

function getXmlFiles(xmlDir: string) {
	const dirents = fs.readdirSync(xmlDir, { withFileTypes: true })
	let xmlFiles = dirents.filter(isXmlFile)
	return xmlFiles.map(dirent => path.resolve(xmlDir, dirent.name))
}

function evaluateFunc(xml: string, xmlFilePath: string) {
	const parser = new DOMParser()
	const xmlDoc = parser.parseFromString(xml, 'application/xml')

	function extractParts(selector: string): Map<string, Element> {
		const chapters: Map<string, Element> = new Map()

		const milestones = xmlDoc.querySelectorAll(selector)
		Array.from(milestones)
			.forEach((milestone, index) => {
				const chapterId = `letter${index + 1}`

				const range = new Range()
				range.setStartAfter(milestone)	
				if (milestones[index + 1] != null) {
					range.setEndBefore(milestones[index + 1])
				}
				else {
					range.setEndAfter(xmlDoc.lastChild)
				}
				const el = document.createElement('div')
				el.appendChild(range.extractContents())
				chapters.set(chapterId, el)
			})

		return chapters
	}

	const serializer = new XMLSerializer()
	function doc2string(doc: Node) {
		return serializer.serializeToString(doc)
			.replace(/\sxmlns="(.*?)"/g, '')
			.replace(/\[/g, '<supplied>')
			.replace(/\]/g, '</supplied>')
	}

	console.log('WE ARE HHERE')

	// @ts-ignore
	for (const p of xmlDoc.querySelectorAll('p')) {
		// Convert <p>/ START LETTER /</p> to <letterStart />
		if (/^\/\s?START\sLETTER\s?\/\s?/.test(p.textContent)) {
			const letterStart = xmlDoc.createElement('letterStart')
			p.parentNode.replaceChild(letterStart, p)
		}

		// Find the span's with textContent "\ 100r \" or "\ 102v \"
		if (/^\/\s?\d+(r|v)\s?\/\s?/.test(p.textContent)) {
			const [id] = /\d+(r|v)/.exec(p.textContent)
			const pb = xmlDoc.createElement('pb')
			pb.setAttribute('xml:id', `f${id}`)
			pb.setAttribute('n', id)
			p.parentNode.replaceChild(pb, p)
		}

		// Add <lb>s
		p.innerHTML = p.innerHTML.replace(/\|/g, '<lb />')

		// Remove empty <p>'s
		if (
			!p.textContent.trim().length ||
			/^(b|B)ianca\s?\.?$/.test(p.textContent.trim())
		) {
			p.parentNode.removeChild(p)
		}
	}

	// Simplify <hi>s (rendition="simple:italic" => rend="italic")
	// @ts-ignore
	for (const hi of xmlDoc.querySelectorAll('hi')) {
		const value = hi.getAttribute('rendition')
		hi.setAttribute('rend', value.replace('simple:', ''))
		hi.removeAttribute('rendition')
	}

	const [,filza,,respName] = xmlFilePath.slice(xmlFilePath.lastIndexOf('/'), -4).split('_')

	const parts = extractParts('letterStart')
	console.log('SIZE', parts.size)
	const output = new Map<string, string>()
	for (const [id, letter] of Array.from(parts.entries())) {
		const notes = new Map()
		Array.from(letter.querySelectorAll('note')).forEach((note, i) => {
			const index = (i + 1).toString()
			const noteId = `tn${index}`
			notes.set(noteId, note)
			const ptr = xmlDoc.createElement('ptr')
			ptr.setAttribute('target', `#${noteId}`)
			ptr.setAttribute('n', index)
			note.parentNode.replaceChild(ptr, note)
		})

		const notesDiv = xmlDoc.createElement('div')
		notesDiv.setAttribute('type', 'transcription_notes')
		for (const [id, note] of Array.from(notes.entries())) {
			note.setAttribute('xml:id', id)
			notesDiv.appendChild(note)
		}

		const letternoResult = /\d+/.exec(letter.querySelector('p:nth-of-type(1)').textContent)
		const letterno = Array.isArray(letternoResult) ? letternoResult[0] : ''

		const p2 = letter.querySelector('p:nth-of-type(2)').textContent.replace(/\n/g, '')
		const biblScopeResult = /\(cc\.\s?(.*)\)/.exec(p2)
		const biblScope = Array.isArray(biblScopeResult) ? biblScopeResult[1] : ''

		const [dateSettlement] = p2.split(' (')
		const [date, settlement] = dateSettlement.split(/,\s?/)
		const normalizedDate = `${date.slice(-4)}-xx-${date.slice(0, 2)}`

		const range = new Range()
		range.setStartAfter(letter.querySelector('p:nth-of-type(4)'))
		range.setEndBefore(letter.querySelector('pb:last-of-type'))
		const original = range.cloneContents()

		// Add an ID to every <p> of the original
		Array.from(original.querySelectorAll('p')).forEach((p,i) => {
			p.setAttribute('xml:id', `p${i + 1}`)
		})

		const start = letter.querySelector('pb:last-of-type') 
		range.setStartBefore(start)
		range.setEndAfter(letter.querySelector('p:last-of-type'))
		const secretarial = range.cloneContents()

		// Add an ID to every <p> of the secretarial
		Array.from(secretarial.querySelectorAll('p')).forEach((p,i) => {
			p.setAttribute('xml:id', `ps${i + 1}`)
		})

		output.set(
			id, 
			`<?xml version="1.0" encoding="utf-8"?>
			<?xml-model href="https://xmlschema.huygens.knaw.nl/suriano.rng" type="application/xml"  schematypens="http://relaxng.org/ns/structure/1.0"?>
			<?xml-model href="https://xmlschema.huygens.knaw.nl/suriano.rng" type="application/xml"  schematypens="http://purl.oclc.org/dsdl/schematron"?>
			<TEI xmlns="http://www.tei-c.org/ns/1.0">
			<teiHeader>
			<fileDesc>
				<titleStmt>
					<title>Letter ${filza}.${letterno} date ${normalizedDate}</title>
					<author>Christofforo Suriano</author>
					<editor xml:id="nl">Nina Lamal</editor>
					<respStmt>
						<resp>transcription</resp>
						<name>${respName}</name>
					</respStmt>
				</titleStmt>
				<publicationStmt>
					<p/>
				</publicationStmt>
				<sourceDesc>
					<msDesc>
						<msIdentifier>
							<settlement>Venice</settlement>
							<institution>Archivio di Stato di Venezia</institution>
							<collection>Senato, Dispacci, Signori Stati</collection>
							<idno type="filza">${filza}</idno>
							<idno type="letterno">${letterno}</idno>
						</msIdentifier>
					</msDesc>
					<bibl>
						<biblScope unit="page">${biblScope}</biblScope>
					</bibl>
				</sourceDesc>
			</fileDesc>
			<profileDesc>
				<correspDesc>
					<correspAction type="sent">
						<name ref="bio.xml#cs">Christofforo Suriano</name>
						<settlement>${settlement}</settlement>
						<date when="${normalizedDate}">${date}</date>
						<num>1</num>
					</correspAction>
				</correspDesc>
			</profileDesc>
			</teiHeader>
			<text>
			<body>
				<div type="original">
					<div type="text">
						${doc2string(original)}
					</div>
					<div type="secretarial">
						${doc2string(secretarial)}
					</div>
				</div>
				<div type="notes">
					<div type="summary">
						<p>
							${letter.querySelector('p:nth-of-type(4)').textContent}
						</p>
					</div>
					${doc2string(notesDiv)}
				</div>
			</body>
			</text>
			</TEI>`
		)
	}

	return Array.from(output)
}

// export default async function main<T, U extends any[]>(evaluateFunc: (...args: U) => T, ...args: U): Promise<T> {
async function main() {
	const browser = await puppeteer.launch({
		args: [
			'--no-sandbox',
			'--disable-setuid-sandbox',
		]
	})

	const page = await browser.newPage()
	page.on('console', (msg: any) => {
		console.log(chalk.blue('< From Puppeteer page >'))
		console.log(msg.text())
		console.log(chalk.blue('^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^\n'))
	})

	const xmlInputDir = path.resolve(process.cwd(), 'input')
	const xmlFiles = getXmlFiles(xmlInputDir)

	console.log(xmlFiles)

	for (const xmlFilePath of xmlFiles) {
		const content = fs.readFileSync(xmlFilePath, 'utf8')
		console.log(content)
		const output = await page.evaluate(evaluateFunc, content, xmlFilePath)

		output.forEach(o => {
			const [id, content] = o
			let p = xmlFilePath.replace(/input/, 'output')
			p = path.resolve(path.dirname(p), path.basename(p, '.xml') + `_${id}` + '.xml') 

			fs.writeFileSync(p, content, 'utf8')
		})
	}

	browser.close()
}

main()
