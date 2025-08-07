# Lisp의 뿌리 (The Roots of Lisp)

2001년 5월

이 글은 제가 McCarthy가 정확히 무엇을 발견했는지 이해하는 데 도움을 주기 위해 썼습니다. Lisp로 프로그래밍하는 데 이 내용을 알 필요는 없지만, Lisp의 기원과 의미론적 핵심 양쪽 모두에서 Lisp의 본질을 이해하고자 하는 모든 이에게 도움이 될 것입니다. Lisp에 그러한 핵심이 있다는 사실은 Lisp를 다른 언어들과 구별하는 특징 중 하나이며, 다른 언어들과 달리 Lisp에 방언(dialects)이 존재하는 이유입니다.

1960년, John McCarthy는 프로그래밍에 있어 유클리드가 기하학에 했던 것과 유사한 일을 해낸 주목할 만한 논문을 발표했습니다. 그는 간단한 연산자 몇 개와 함수 표기법만으로 전체 프로그래밍 언어를 구축할 수 있음을 보여주었습니다.

그는 이 언어를 "List Processing", 즉 리스트 처리의 약자인 Lisp라고 명명했습니다. 왜냐하면 그의 핵심 아이디어 중 하나는 코드와 데이터 양쪽 모두에 리스트(list)라는 간단한 자료 구조를 사용하는 것이었기 때문입니다.

McCarthy가 발견한 것을 컴퓨터 역사에서의 이정표로서뿐만 아니라, 우리 시대의 프로그래밍이 지향하는 바에 대한 모델로서 이해할 가치가 있습니다. 제 생각에 지금까지 프로그래밍에는 두 가지 정말 깔끔하고 일관된 모델이 있었습니다: 바로 C 모델과 Lisp 모델입니다.

이 둘은 그 사이에 습지 같은 저지대가 있는 높은 지점처럼 보입니다. 컴퓨터가 더욱 강력해짐에 따라, 새롭게 개발되는 언어들은 꾸준히 Lisp 모델을 향해 나아가고 있습니다. 지난 20년간 새로운 프로그래밍 언어에 대한 인기 있는 방식은 컴퓨팅의 C 모델을 가져와서, 런타임 타이핑(runtime typing)과 가비지 컬렉션(garbage collection) 같은 Lisp 모델의 부분들을 조금씩 추가하는 것이었습니다.

이 글에서는 McCarthy가 무엇을 발견했는지 가능한 가장 쉬운 용어로 설명해 보겠습니다. 단순히 40년 전에 누군가가 알아낸 흥미로운 이론적 결과에 대해 배우는 것이 목적이 아니라, 언어들이 어디로 향하고 있는지를 보여주는 것이 목적입니다.

Lisp의 특이한 점, 사실상 Lisp를 정의하는 특성은 Lisp가 자기 자신으로 작성될 수 있다는 것입니다. McCarthy가 이것으로 무엇을 의미했는지 이해하기 위해, 그의 수학적 표기법을 실행되는 커먼 리스프(Common Lisp) 코드로 변환하여 그의 단계를 따라가 보겠습니다.

- [Complete Article (Postscript)](https://sep.turbifycdn.com/ty/cdn/paulgraham/jmc.ps?t=1688221954&)
- [What Made Lisp Different](https://mephisto405.github.io/paulgraham-essay/essay_template.html?essay=diff)
- [The Code](https://sep.turbifycdn.com/ty/cdn/paulgraham/jmc.lisp?t=1688221954&)