import { Card, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"


export const UserManual = () => {


  return (
    <div className="flex justify-evenly align-middle py-4">
      <Card className="w-[350px]">
        <CardHeader>
          <CardTitle className="flex justify-between align-baseline">
            Lorem TITLE
          </CardTitle>
          <CardDescription>Lorem ipsum</CardDescription>
        </CardHeader>
        <CardFooter className="flex justify-end py-6">
        </CardFooter>
      </Card>

      <Card className="w-[350px]">
        <CardHeader>
          <CardTitle className="flex justify-between align-baseline">
            Lorem TITLE
          </CardTitle>
          <CardDescription>Lorem ipsum</CardDescription>
        </CardHeader>
        <CardFooter className="flex justify-end py-6">
        </CardFooter>
      </Card>

      <Card className="w-[350px]">
        <CardHeader>
          <CardTitle className="flex justify-between align-baseline">
            Lorem TITLE
          </CardTitle>
          <CardDescription>Lorem ipsum</CardDescription>
        </CardHeader>
        <CardFooter className="flex justify-end py-6">
        </CardFooter>
      </Card>
    </div>
  )
}