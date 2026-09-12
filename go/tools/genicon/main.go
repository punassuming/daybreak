// Command genicon renders Daybreak's existing sun-icon pixel art (the
// same math used for the tray icon, tray.RenderModeIconPixels) into a
// proper multi-resolution Windows .ico, so the app icon and the tray icon
// come from the same source of truth instead of a separately hand-drawn
// asset. Not part of the release build — run once (or whenever the icon
// design changes) to regenerate go/assets/daybreak.ico, which IS checked
// in and used by winres.json to embed the icon into daybreak.exe and
// daybreak-tray.exe.
//
//	go run ./tools/genicon
package main

import (
	"bytes"
	"encoding/binary"
	"image"
	"image/png"
	"log"
	"os"

	"daybreak/internal/tray"
)

var sizes = []int{16, 24, 32, 48, 64, 128, 256}

func main() {
	var entries [][]byte
	for _, size := range sizes {
		png, err := renderPNG(size)
		if err != nil {
			log.Fatalf("render %dx%d: %v", size, size, err)
		}
		entries = append(entries, png)
	}

	out, err := writeICO(sizes, entries)
	if err != nil {
		log.Fatal(err)
	}

	if err := os.WriteFile("assets/daybreak.ico", out, 0o644); err != nil {
		log.Fatal(err)
	}
	log.Println("wrote assets/daybreak.ico")
}

func renderPNG(size int) ([]byte, error) {
	bgra := tray.RenderModeIconPixels("light", size)
	img := image.NewNRGBA(image.Rect(0, 0, size, size))
	for i := 0; i < size*size; i++ {
		b, g, r, a := bgra[i*4], bgra[i*4+1], bgra[i*4+2], bgra[i*4+3]
		img.Pix[i*4] = r
		img.Pix[i*4+1] = g
		img.Pix[i*4+2] = b
		img.Pix[i*4+3] = a
	}

	var buf bytes.Buffer
	if err := png.Encode(&buf, img); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// writeICO builds a Vista+ style .ico container (ICONDIR + ICONDIRENTRY
// per size) with PNG-encoded image data in each entry, which every current
// Windows version accepts alongside (or instead of) legacy raw-BMP entries.
func writeICO(sizes []int, pngBlobs [][]byte) ([]byte, error) {
	var buf bytes.Buffer

	// ICONDIR
	binary.Write(&buf, binary.LittleEndian, uint16(0)) // reserved
	binary.Write(&buf, binary.LittleEndian, uint16(1)) // type: icon
	binary.Write(&buf, binary.LittleEndian, uint16(len(sizes)))

	headerSize := 6 + 16*len(sizes)
	offset := headerSize

	for i, size := range sizes {
		dim := byte(size)
		if size >= 256 {
			dim = 0 // 0 means 256 in ICO format
		}
		buf.WriteByte(dim)                                  // width
		buf.WriteByte(dim)                                  // height
		buf.WriteByte(0)                                    // color count (0 = no palette)
		buf.WriteByte(0)                                    // reserved
		binary.Write(&buf, binary.LittleEndian, uint16(1))  // planes
		binary.Write(&buf, binary.LittleEndian, uint16(32)) // bit count
		binary.Write(&buf, binary.LittleEndian, uint32(len(pngBlobs[i])))
		binary.Write(&buf, binary.LittleEndian, uint32(offset))
		offset += len(pngBlobs[i])
	}

	for _, blob := range pngBlobs {
		buf.Write(blob)
	}

	return buf.Bytes(), nil
}
