const photos = [
  { name: "open-road", alt: "A dark semi-truck and trailer beside open plains", position: "center 78%" },
  { name: "red-truck", alt: "Close view of a red Kenworth truck and chrome grille", position: "center 70%" },
  { name: "highway", alt: "Freight trucks following a highway through the countryside", position: "center 76%" },
];

export const TruckingGallery = () => <div className="trucking-gallery no-print" data-testid="trucking-gallery">
  {photos.map((photo, index) => <figure key={photo.name} className={`trucking-photo ${index === 0 ? "trucking-photo-main" : ""}`}>
    <img data-testid={`trucking-photo-${photo.name}`} src={`${process.env.PUBLIC_URL}/images/trucking/${photo.name}.webp`} alt={photo.alt} style={{ objectPosition: photo.position }} decoding="async" fetchPriority={index === 0 ? "high" : "auto"} />
  </figure>)}
</div>;