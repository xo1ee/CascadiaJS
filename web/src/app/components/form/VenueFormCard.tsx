// import { AddressSearchField } from "./AddressSearchField";
// import { FormField } from "./FormField";
// import { VenueAnalysis, VenueInput } from "@/lib/types";

// // form placeholders
// const VENUE_PLACEHOLDERS: Pick<VenueInput, "name" | "address">[] = [
//     {
//       name: "thinkspace Seattle",
//       address: "1700 Westlake Ave N #200, Seattle, WA 98109",
//     },
//     {
//       name: "Impact Hub Seattle",
//       address: "220 2nd Ave S, Seattle, WA 98104",
//     },
//   ];
  
// const venueCardClassName =
// "space-y-5 rounded-xl border border-zinc-100 bg-zinc-50/80 p-5 dark:border-zinc-800 dark:bg-zinc-950/50";


// export function VenueFormCard({
//     venue,
//     index,
//     onUpdate,
//     onRemove,
//     canRemove,
//   }: {
//     venue: VenueInput;   
//     index: number;
//     onUpdate: (id: string, field: keyof Pick<VenueInput, "name" | "address">, value: string) => void;
//     onRemove: (id: string) => void;
//     canRemove: boolean;
//   }) {
//     const placeholders = VENUE_PLACEHOLDERS[index] ?? {
//       name: "Venue name",
//       address: "Street address, city, state, zip",
//     };
  
//     return (
//       <div className={venueCardClassName}>
//         <div className="flex items-center justify-between gap-2">
//           <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
//             Venue {index + 1}
//           </p>
//           {canRemove ? (
//             <button
//               type="button"
//               onClick={() => onRemove(venue.id)}
//               className="text-xs font-medium text-zinc-500 transition hover:text-red-600 dark:text-zinc-400 dark:hover:text-red-400"
//             >
//               Remove
//             </button>
//           ) : null}
//         </div>
//         <FormField
//           id={`${venue.id}-name`}
//           label="Name"
//           name="name"
//           value={venue.name}
//           onChange={(e) => onUpdate(venue.id, "name", e.target.value)}
//           placeholder={placeholders.name}
//         />
//         <AddressSearchField
//           id={`${venue.id}-address`}
//           label="Address"
//           value={venue.address}
//           onChange={(address) => onUpdate(venue.id, "address", address)}
//           placeholder={placeholders.address}
//         />
//       </div>
//     );
//   }
  
  
// function VenueInputCard({
//     venue,
//     index,
//     onUpdate,
//     onRemove,
//     canRemove,
//   }: {
//     venue: VenueInput;
//     index: number;
//     onUpdate: (id: string, field: keyof Pick<VenueInput , "name" | "address">, value: string) => void;
//     onRemove: (id: string) => void;
//     canRemove: boolean;
//   }) {
//     const venueInputCardClassName =
//     "space-y-5 rounded-xl border border-zinc-100 bg-zinc-50/80 p-5 dark:border-zinc-800 dark:bg-zinc-950/50";

//     const placeholders = VENUE_PLACEHOLDERS[index] ?? {
//       name: "Venue name",
//       address: "Street address, city, state, zip",
//     };
  
//     return (
//       <div className={venueInputCardClassName}>
//         <div className="flex items-center justify-between gap-2">
//           <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
//             Venue {index + 1}
//           </p>
//           {canRemove ? (
//             <button
//               type="button"
//               onClick={() => onRemove(venue.id)}
//               className="text-xs font-medium text-zinc-500 transition hover:text-red-600 dark:text-zinc-400 dark:hover:text-red-400"
//             >
//               Remove
//             </button>
//           ) : null}
//         </div>
//         <FormField
//           id={`${venue.id}-name`}
//           label="Name"
//           name="name"
//           value={venue.name}
//           onChange={(e) => onUpdate(venue.id, "name", e.target.value)}
//           placeholder={placeholders.name}
//         />
//         <AddressSearchField
//           id={`${venue.id}-address`}
//           label="Address"
//           value={venue.address}
//           onChange={(address) => onUpdate(venue.id, "address", address)}
//           placeholder={placeholders.address}
//         />
//       </div>
//     );
//   }
  
//   function VenueComparisonCard({
//     venue,
//     index,
//     analysis,
//     className = "min-w-0",
//   }: {
//     venue: VenueInput;
//     index: number;
//     analysis?: VenueAnalysis;
//     className?: string;
//   }) {
//     const displayName = venue.name.trim() || analysis?.name || `Venue ${index + 1}`;
//     const displayDescription =
//       analysis?.summary?.trim() ||
//       "Comparison summary will appear here after generation.";
  
//     return (    
//     <div className={`${venueCardClassName} ${className}`}>
//         <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
//           Venue {index + 1}
//         </p>
//         <p className="text-sm text-zinc-800 dark:text-zinc-200">{displayName}</p>
//         <p className="text-xs text-zinc-500 dark:text-zinc-400">{displayDescription}</p>
//       </div>
//     );
//   }