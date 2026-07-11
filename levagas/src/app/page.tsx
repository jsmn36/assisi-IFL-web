import { Hero } from "@/components/home/Hero";
import { AboutHome } from "@/components/home/AboutHome";
import { FeaturedCottages } from "@/components/home/FeaturedCottages";
import { ExperiencesHome } from "@/components/home/ExperiencesHome";
import { ReviewsHome } from "@/components/home/ReviewsHome";
import { InstagramHome } from "@/components/home/InstagramHome";
import { FinalCTA } from "@/components/home/FinalCTA";

export default function Home() {
  return (
    <>
      <Hero />
      <AboutHome />
      <FeaturedCottages />
      <ExperiencesHome />
      <ReviewsHome />
      <InstagramHome />
      <FinalCTA />
    </>
  );
}
